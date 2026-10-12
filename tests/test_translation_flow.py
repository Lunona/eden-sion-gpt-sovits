import unittest, sys, json, tempfile, threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import translation
import app

SOURCE='你好。今天试着用一段短文字生成语音。'
JAPANESE='こんにちは。今日は、短い文章から音声を作ってみます。'

class Handler(BaseHTTPRequestHandler):
    answer=JAPANESE
    status=200
    finish_reason='stop'
    calls=[]
    def log_message(self,*args):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.calls.append((self.path,body,self.headers.get('Authorization')))
        self.send_response(self.status);self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps({'choices':[{'message':{'content':self.answer},'finish_reason':self.finish_reason}]}).encode())

class TranslationFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.endpoint=f'http://127.0.0.1:{cls.server.server_port}/v1'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def setUp(self):Handler.answer=JAPANESE;Handler.status=200;Handler.finish_reason='stop';Handler.calls.clear()
    def test_japanese_bypasses_translation_even_with_no_config(self):
        with patch.object(translation,'translate_chinese',side_effect=AssertionError('should not translate')):
            text,route,_=translation.prepare_text(JAPANESE,'自动')
        self.assertEqual((text,route),(JAPANESE,'ja'))
    def test_language_ambiguity_and_manual_override(self):
        route,note=translation.language_route('了解','自动')
        self.assertEqual(route,'zh');self.assertIn('纯汉字日文',note)
        self.assertEqual(translation.language_route('了解','日文')[0],'ja')
        self.assertEqual(translation.language_route('今日は你好','中文')[0],'zh')
    def test_empty_unknown_and_long_inputs(self):
        for text in ['', 'hello 123', '你'*2001]:
            with self.assertRaises(translation.TranslationError):translation.language_route(text,'自动')
    def test_chinese_http_utf8_and_auth(self):
        result=translation.prepare_text(SOURCE,'自动',self.endpoint,'test-fixture','test-secret')
        self.assertEqual(result[:2],(JAPANESE,'zh'))
        path,body,auth=Handler.calls[0]
        self.assertEqual(path,'/v1/chat/completions');self.assertEqual(body['messages'][1]['content'],SOURCE)
        self.assertEqual(auth,'Bearer test-secret')
    def test_missing_config_never_calls_speech(self):
        with patch.object(app,'generate') as speech:
            result=app.generate_with_translation('baseline',SOURCE,True,1,'自动','','','','',None)
        speech.assert_not_called();self.assertIsNone(result[0]);self.assertIn('翻译服务',result[3])
    def test_translation_errors_never_call_speech_or_leak_key(self):
        for status in [401,403,404,429,500]:
            Handler.status=status
            with patch.object(app,'generate') as speech:
                result=app.generate_with_translation('baseline',SOURCE,True,1,'中文',self.endpoint,'fixture','test-secret','old-stale-text',None)
            speech.assert_not_called();self.assertIsNone(result[0]);self.assertEqual(result[1],'');self.assertNotIn('test-secret',result[3])
    def test_bad_chinese_empty_and_truncated_responses(self):
        for answer,finish in [(SOURCE,'stop'),('','stop'),(JAPANESE,'length'),('```'+JAPANESE+'```','stop')]:
            Handler.answer=answer;Handler.finish_reason=finish
            with self.assertRaises(translation.TranslationError):translation.prepare_text(SOURCE,'中文',self.endpoint,'fixture')
    def test_url_validation_and_redirect_block(self):
        for endpoint in ['file:///temp/key','http://example.com/v1','https://key:secret@example.com/v1','https://example.com/v1?key=secret']:
            with self.assertRaises(translation.TranslationError):translation.completion_url(endpoint)
        self.assertIsNone(translation.NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.test'))
    def test_preview_edit_used_without_retranslating(self):
        japanese,state,_,_=app.prepare_preview(SOURCE,'中文',self.endpoint,'fixture','test-secret')
        edited='こんにちは。今日は声を作ってみます。'
        with patch.object(app,'generate',return_value=('unused.wav','success')) as speech:
            result=app.generate_with_translation('baseline',SOURCE,True,1,'中文',self.endpoint,'fixture','test-secret',edited,state)
        speech.assert_called_once_with('baseline',edited,True,1);self.assertEqual(len(Handler.calls),1);self.assertEqual(result[1],edited)
    def test_changed_source_does_not_use_stale_preview(self):
        _,state,_,_=app.prepare_preview(SOURCE,'中文',self.endpoint,'fixture','')
        changed='谢谢你。';Handler.answer='ありがとうございます。'
        with patch.object(app,'generate',return_value=('unused.wav','success')) as speech:
            result=app.generate_with_translation('baseline',changed,True,1,'中文',self.endpoint,'fixture','',JAPANESE,state)
        speech.assert_called_once_with('baseline','ありがとうございます。',True,1);self.assertEqual(len(Handler.calls),2)
    def test_generation_provenance_contains_no_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'voice.wav';file.with_suffix('.json').write_text('{}')
            with patch.object(app,'generate',return_value=(str(file),'success')) as speech:
                result=app.generate_with_translation('baseline',SOURCE,True,1,'中文',self.endpoint,'fixture','test-secret','',None)
            speech.assert_called_once_with('baseline',JAPANESE,True,1)
            metadata=file.with_suffix('.json').read_text(encoding='utf-8')
            self.assertNotIn('test-secret',metadata);self.assertNotIn(self.endpoint,metadata)
            self.assertEqual(json.loads(metadata)['source_text'],SOURCE);self.assertEqual(result[1],JAPANESE)
    def test_direct_japanese_generation(self):
        with patch.object(app,'generate',return_value=('unused.wav','success')) as speech:
            result=app.generate_with_translation('baseline',JAPANESE,True,1,'自动','','','','',None)
        speech.assert_called_once_with('baseline',JAPANESE,True,1);self.assertEqual(Handler.calls,[])

if __name__=='__main__':unittest.main(verbosity=2)
