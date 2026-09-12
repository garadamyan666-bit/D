import base64
import io
from dataclasses import replace
import requests
import pytest
from PIL import Image
from app.services import chart_vision as vision


def chart():
    data=io.BytesIO()
    Image.new('RGB',(800,600),'white').save(data,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(data.getvalue()).decode()


def test_gemini_image_wire_format_and_no_thoughts(monkeypatch):
    monkeypatch.setattr(vision,'settings',replace(vision.settings,gemini_api_key='test-secret'))
    def post(url, **kwargs):
        assert 'test-secret' not in url
        assert kwargs['headers']['x-goog-api-key']=='test-secret'
        assert 'inlineData' in kwargs['json']['contents'][0]['parts'][1]
        assert kwargs['json']['store'] is False
        class Response:
            def raise_for_status(self): pass
            def json(self): return {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'private','thought':True},{'text':'WAIT'}]}}]}
        return Response()
    monkeypatch.setattr(vision.requests,'post',post)
    assert vision.analyze_chart(chart(),'EUR/USD','M1')=='WAIT'


@pytest.mark.parametrize('status',[400,401,403,404,429,500])
def test_errors_never_leak_provider_payload_or_fallback(monkeypatch,status):
    monkeypatch.setattr(vision,'settings',replace(vision.settings,gemini_api_key='secret-value'))
    calls=[]
    def post(*args,**kwargs):
        calls.append(1)
        response=requests.Response();response.status_code=status
        raise requests.HTTPError('secret-value sensitive provider error',response=response)
    monkeypatch.setattr(vision.requests,'post',post)
    with pytest.raises(vision.ChartVisionError) as error:
        vision.analyze_chart(chart(),'EUR/USD','M1')
    assert 'secret-value' not in str(error.value)
    assert len(calls)==1


def test_missing_key_does_not_send_image(monkeypatch):
    monkeypatch.setattr(vision,'settings',replace(vision.settings,gemini_api_key=''))
    monkeypatch.setattr(vision.requests,'post',lambda *a,**k:pytest.fail('No key'))
    with pytest.raises(vision.ChartVisionError,match='GEMINI_API_KEY'):
        vision.analyze_chart(chart(),'EUR/USD','M1')
