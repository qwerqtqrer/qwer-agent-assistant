"""工具健壮性测试：LLM 失败时回退到原始数据。"""

from types import SimpleNamespace

from app.tools import campus, weather


def test_weather_beautify_falls_back_on_llm_error(monkeypatch):
    monkeypatch.setattr(weather, "config", SimpleNamespace(llm_configured=True))

    def boom(*args, **kwargs):
        raise RuntimeError("api down")

    monkeypatch.setattr(weather, "build_llm", boom)
    text = weather._beautify_weather(
        {
            "location": "大理",
            "date": "2026-08-15",
            "weather": "晴",
            "temperature": "25°C",
            "humidity": "50%",
        }
    )
    assert "当前城市：大理" in text
    assert "出行建议" in text


def test_campus_beautify_falls_back_to_raw_data(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("api down")

    monkeypatch.setattr(campus, "build_llm", boom)
    text = campus._beautify("整理数据", fallback="原始数据")
    assert "原始数据" in text
