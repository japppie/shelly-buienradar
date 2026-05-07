import pytest
import responses
import requests
from unittest import mock
from src.shelly_buienradar.core import (
    get_config,
    fetch_with_retries,
    check_device_status,
    check_wind,
    check_buienradar,
    check_rain,
    close_sunscreen,
    check_and_close_sunscreen,
)


@pytest.fixture
def mock_config():
    return {
        "api_url": "http://api.shelly.cloud/close",
        "test_url": "http://api.shelly.cloud/status",
        "device_id": "test_device",
        "auth_key": "test_auth",
        "weerlive_key": "test_weerlive",
        "lat": "12.34",
        "lon": "56.78",
    }


@mock.patch.dict(
    "os.environ",
    {"API_URL": "http://env.url", "SHELLY_AUTH": "env_auth", "AUTH_KEY": ""},
)
def test_get_config_cloud():
    config = get_config(is_cloud=True)
    assert config["api_url"] == "http://env.url"
    assert config["auth_key"] == "env_auth"


@mock.patch("dotenv.load_dotenv")
@mock.patch.dict(
    "os.environ", {"API_URL": "http://local.url", "AUTH_KEY": "local_auth"}
)
def test_get_config_local(mock_load_dotenv):
    config = get_config(is_cloud=False)
    mock_load_dotenv.assert_called_once()
    assert config["api_url"] == "http://local.url"
    assert config["auth_key"] == "local_auth"


@responses.activate
@mock.patch("time.sleep")
def test_fetch_with_retries_success(mock_sleep):
    responses.add(responses.GET, "http://test.url", json={"status": "ok"}, status=200)
    response = fetch_with_retries("http://test.url")
    assert response.json() == {"status": "ok"}
    mock_sleep.assert_not_called()


@responses.activate
@mock.patch("time.sleep")
def test_fetch_with_retries_fail_then_success(mock_sleep):
    responses.add(responses.GET, "http://test.url", status=500)
    responses.add(responses.GET, "http://test.url", json={"status": "ok"}, status=200)
    response = fetch_with_retries("http://test.url")
    assert response.json() == {"status": "ok"}
    mock_sleep.assert_called_once_with(2)


@responses.activate
@mock.patch("time.sleep")
def test_fetch_with_retries_fail_all(mock_sleep):
    responses.add(responses.GET, "http://test.url", status=500)
    responses.add(responses.GET, "http://test.url", status=500)
    responses.add(responses.GET, "http://test.url", status=500)
    response = fetch_with_retries("http://test.url", retries=3)
    assert response is None
    assert mock_sleep.call_count == 2


@responses.activate
@mock.patch("time.sleep")
def test_fetch_with_retries_request_exception(mock_sleep):
    responses.add(
        responses.GET,
        "http://test.url",
        body=requests.exceptions.ConnectionError("Connection error"),
    )
    response = fetch_with_retries("http://test.url", retries=1)
    assert response is None


@responses.activate
def test_check_device_status_success(mock_config):
    responses.add(
        responses.GET,
        "http://api.shelly.cloud/status",
        json={"data": {"device_status": {"cover:0": {"current_pos": 50}}}},
        status=200,
    )
    status = check_device_status(mock_config)
    assert status == 50


@responses.activate
def test_check_device_status_error(mock_config):
    responses.add(
        responses.GET, "http://api.shelly.cloud/status", json={"data": {}}, status=200
    )
    status = check_device_status(mock_config)
    assert status == 100


@responses.activate
def test_check_device_status_network_error(mock_config):
    responses.add(responses.GET, "http://api.shelly.cloud/status", status=500)
    status = check_device_status(mock_config)
    assert status == 100


@responses.activate
def test_check_wind_success(mock_config):
    responses.add(
        responses.GET,
        "https://weerlive.nl/api/weerlive_api_v2.php?key=test_weerlive&locatie=Arnhem",
        json={"liveweer": [{"windbft": 5, "windkmh": 35}]},
        status=200,
    )
    wind_bft, wind_kmh = check_wind(mock_config)
    assert wind_bft == 5
    assert wind_kmh == 35


@responses.activate
def test_check_wind_error(mock_config):
    responses.add(
        responses.GET,
        "https://weerlive.nl/api/weerlive_api_v2.php?key=test_weerlive&locatie=Arnhem",
        json={"error": "true"},
        status=200,
    )
    wind_bft, wind_kmh = check_wind(mock_config)
    assert wind_bft == 0
    assert wind_kmh == 0


@responses.activate
def test_check_wind_network_error(mock_config):
    responses.add(
        responses.GET,
        "https://weerlive.nl/api/weerlive_api_v2.php?key=test_weerlive&locatie=Arnhem",
        status=500,
    )
    wind_bft, wind_kmh = check_wind(mock_config)
    assert wind_bft == 0
    assert wind_kmh == 0


@responses.activate
def test_check_buienradar_success(mock_config):
    rain_text = "000|14:00\n020|14:05\n000|14:10\n000|14:15\n000|14:20\n"
    responses.add(
        responses.GET,
        "https://gadgets.buienradar.nl/data/raintext/?lat=12.34&lon=56.78",
        body=rain_text,
        status=200,
    )
    rain_values = check_buienradar(mock_config)
    assert rain_values == [0, 20, 0, 0, 0]


@responses.activate
def test_check_buienradar_parse_error(mock_config):
    rain_text = "invalid_data\n"
    responses.add(
        responses.GET,
        "https://gadgets.buienradar.nl/data/raintext/?lat=12.34&lon=56.78",
        body=rain_text,
        status=200,
    )
    rain_values = check_buienradar(mock_config)
    assert rain_values is None


@responses.activate
def test_check_buienradar_network_error(mock_config):
    responses.add(
        responses.GET,
        "https://gadgets.buienradar.nl/data/raintext/?lat=12.34&lon=56.78",
        status=500,
    )
    rain_values = check_buienradar(mock_config)
    assert rain_values is None


def test_check_rain():
    assert check_rain([0, 0, 0, 0, 0]) is False
    assert check_rain([1, 0, 0, 0, 0]) is True  # raining now
    assert check_rain([0, 0, 11, 11, 11]) is True  # rain soon (avg 11)
    assert check_rain([0, 0, 10, 10, 10]) is False  # not quite soon (avg 10)
    assert check_rain([0, 0]) is False  # not enough data
    assert check_rain(None) is False  # none check


@responses.activate
@mock.patch("time.sleep")
def test_close_sunscreen_success(mock_sleep, mock_config):
    responses.add(
        responses.POST, "http://api.shelly.cloud/close", json={"isok": True}, status=200
    )
    success = close_sunscreen(mock_config)
    assert success is True
    mock_sleep.assert_called_with(2)


@responses.activate
@mock.patch("time.sleep")
def test_close_sunscreen_error_from_api(mock_sleep, mock_config):
    responses.add(
        responses.POST,
        "http://api.shelly.cloud/close",
        json={"isok": False},
        status=200,
    )
    success = close_sunscreen(mock_config)
    assert success is False


@responses.activate
@mock.patch("time.sleep")
def test_close_sunscreen_json_error(mock_sleep, mock_config):
    responses.add(
        responses.POST, "http://api.shelly.cloud/close", body="invalid_json", status=200
    )
    success = close_sunscreen(mock_config)
    assert success is False


@responses.activate
@mock.patch("time.sleep")
def test_close_sunscreen_network_error(mock_sleep, mock_config):
    responses.add(responses.POST, "http://api.shelly.cloud/close", status=500)
    success = close_sunscreen(mock_config)
    assert success is False


@mock.patch("src.shelly_buienradar.core.close_sunscreen")
@mock.patch("src.shelly_buienradar.core.check_device_status")
@mock.patch("src.shelly_buienradar.core.check_wind")
@mock.patch("src.shelly_buienradar.core.check_rain")
@mock.patch("src.shelly_buienradar.core.check_buienradar")
@mock.patch("src.shelly_buienradar.core.get_config")
def test_check_and_close_sunscreen_closes_due_to_wind(
    mock_get_config,
    mock_check_buienradar,
    mock_check_rain,
    mock_check_wind,
    mock_check_device_status,
    mock_close_sunscreen,
    mock_config,
):
    mock_get_config.return_value = mock_config
    mock_check_buienradar.return_value = [0, 0, 0, 0, 0]
    mock_check_rain.return_value = False
    mock_check_wind.return_value = (5, 35)  # bft 5
    mock_check_device_status.return_value = 50  # open

    check_and_close_sunscreen()

    mock_close_sunscreen.assert_called_once_with(mock_config)


@mock.patch("src.shelly_buienradar.core.close_sunscreen")
@mock.patch("src.shelly_buienradar.core.check_device_status")
@mock.patch("src.shelly_buienradar.core.check_wind")
@mock.patch("src.shelly_buienradar.core.check_rain")
@mock.patch("src.shelly_buienradar.core.check_buienradar")
@mock.patch("src.shelly_buienradar.core.get_config")
def test_check_and_close_sunscreen_closes_due_to_rain(
    mock_get_config,
    mock_check_buienradar,
    mock_check_rain,
    mock_check_wind,
    mock_check_device_status,
    mock_close_sunscreen,
    mock_config,
):
    mock_get_config.return_value = mock_config
    mock_check_buienradar.return_value = [10, 0, 0, 0, 0]
    mock_check_rain.return_value = True
    mock_check_wind.return_value = (2, 10)  # bft 2
    mock_check_device_status.return_value = 50  # open

    check_and_close_sunscreen()

    mock_close_sunscreen.assert_called_once_with(mock_config)


@mock.patch("src.shelly_buienradar.core.close_sunscreen")
@mock.patch("src.shelly_buienradar.core.check_device_status")
@mock.patch("src.shelly_buienradar.core.check_wind")
@mock.patch("src.shelly_buienradar.core.check_rain")
@mock.patch("src.shelly_buienradar.core.check_buienradar")
@mock.patch("src.shelly_buienradar.core.get_config")
def test_check_and_close_sunscreen_no_action_needed(
    mock_get_config,
    mock_check_buienradar,
    mock_check_rain,
    mock_check_wind,
    mock_check_device_status,
    mock_close_sunscreen,
    mock_config,
):
    mock_get_config.return_value = mock_config
    mock_check_buienradar.return_value = [0, 0, 0, 0, 0]
    mock_check_rain.return_value = False
    mock_check_wind.return_value = (2, 10)  # bft 2
    mock_check_device_status.return_value = 50  # open

    check_and_close_sunscreen()

    mock_close_sunscreen.assert_not_called()


@mock.patch("src.shelly_buienradar.core.close_sunscreen")
@mock.patch("src.shelly_buienradar.core.check_device_status")
@mock.patch("src.shelly_buienradar.core.check_wind")
@mock.patch("src.shelly_buienradar.core.check_rain")
@mock.patch("src.shelly_buienradar.core.check_buienradar")
@mock.patch("src.shelly_buienradar.core.get_config")
def test_check_and_close_sunscreen_already_closed(
    mock_get_config,
    mock_check_buienradar,
    mock_check_rain,
    mock_check_wind,
    mock_check_device_status,
    mock_close_sunscreen,
    mock_config,
):
    mock_get_config.return_value = mock_config
    mock_check_buienradar.return_value = [10, 0, 0, 0, 0]
    mock_check_rain.return_value = True
    mock_check_wind.return_value = (5, 35)  # bft 5
    mock_check_device_status.return_value = 0  # closed

    check_and_close_sunscreen()

    mock_close_sunscreen.assert_not_called()


@mock.patch("src.shelly_buienradar.core.close_sunscreen")
@mock.patch("src.shelly_buienradar.core.get_config")
def test_check_and_close_sunscreen_missing_config(
    mock_get_config, mock_close_sunscreen
):
    mock_get_config.return_value = {
        "api_url": None,
        "test_url": None,
        "device_id": None,
        "auth_key": None,
        "weerlive_key": None,
        "lat": None,
        "lon": None,
    }
    check_and_close_sunscreen()
    mock_close_sunscreen.assert_not_called()
