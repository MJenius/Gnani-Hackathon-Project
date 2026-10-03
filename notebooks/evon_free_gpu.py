"""Zero-cost interactive notebook experiment. No local model download or public tunnel.

Run only in a free Kaggle/Colab notebook. Public GGUF files need no HF token.
Import this module, then call experiment(schema) with DriveOS's Plan JSON schema.
"""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

REPO = 'luminenio/gnani-evon-v3.3-30B-A3B-GGUF'
REVISION = 'ac033ad46d98503787500e0cb2295897b0b8c03b'
LLAMA_REVISION = '8b4b3558f1459c13e4aa38d5c94d306a00dc6acd'
QUANTS = {
    'Q3_K_S': (16.84, '7d0ea8354cd54d218fe857654a016ecb42f6fb557f918ed3c4e2d799691358c2'),
    'Q3_K_M': (18.62, '457c2e2073d1693e32310c501f8a8288bc4d6dbe6b3bd23fbccf96d985d2afdf'),
    'IQ4_XS': (17.09, '7c8da7b07a8c9f87824e8e3664b880c00d6df9b7eeccaf22f2f5e4208a6f4610'),
}
ROOT = Path('/tmp/driveos-evon')
CASES = [('en-IN', 'Tell Ananya I am 25 minutes late.'),
         ('kn-IN', 'ನಾನು ಇಪ್ಪತ್ತೈದು ನಿಮಿಷ ತಡವಾಗುತ್ತೇನೆ ಎಂದು ಅನನ್ಯ ಅವರಿಗೆ ತಿಳಿಸಿ.')]

def preflight():
    if platform.system() != 'Linux' or not (Path('/kaggle').exists() or Path('/content').exists()):
        raise RuntimeError('This experiment runs only inside a free Kaggle or Colab notebook; no local download')
    ROOT.mkdir(parents=True, exist_ok=True)
    memory = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    available = int(memory['MemAvailable'].split()[0])/1024**2
    command = subprocess.run(['nvidia-smi','--query-gpu=memory.free,compute_cap','--format=csv,noheader,nounits'],
                             capture_output=True,text=True) if shutil.which('nvidia-smi') else None
    gpus = [tuple(float(value.strip()) for value in line.split(','))
            for line in command.stdout.strip().splitlines()] if command and command.returncode == 0 else []
    result = {'environment':'kaggle' if Path('/kaggle').exists() else 'colab',
              'ram_available_gib':round(available,2),'disk_free_gib':round(shutil.disk_usage(ROOT).free/2**30,2),
              'gpu_free_mib':[item[0] for item in gpus], 'compute_capabilities':[item[1] for item in gpus]}
    print(json.dumps(result))
    return result

def build(hardware):
    source=ROOT/'llama.cpp'
    if not source.exists():
        subprocess.run(['git','clone','--filter=blob:none','--no-checkout','https://github.com/ggml-org/llama.cpp.git',str(source)],check=True)
    subprocess.run(['git','-C',str(source),'checkout',LLAMA_REVISION],check=True)
    options=['cmake','-S',str(source),'-B',str(source/'build'),'-DCMAKE_BUILD_TYPE=Release','-DLLAMA_CURL=OFF']
    if hardware['gpu_free_mib']:
        if not shutil.which('nvcc'): raise RuntimeError('CUDA compiler unavailable in this notebook')
        architectures=';'.join(str(int(round(cap*10))) for cap in sorted(set(hardware['compute_capabilities'])))
        options+=['-DGGML_CUDA=ON','-DCMAKE_CUDA_ARCHITECTURES='+architectures]
    else:
        options+=['-DGGML_CUDA=OFF']
    subprocess.run(options,check=True)
    subprocess.run(['cmake','--build',str(source/'build'),'--config','Release','-j','2','--target','llama-server'],check=True)
    return source/'build/bin/llama-server'

def download(quant):
    size,expected=QUANTS[quant]
    folder=ROOT/'models'; folder.mkdir(exist_ok=True)
    model=folder/f'gnani-evon-v3.3-30B-A3B-{quant}.gguf'
    if not model.exists():
        if shutil.disk_usage(folder).free/2**30 < size+3:
            raise RuntimeError('Insufficient scratch disk for selected quant and build overhead')
        partial=model.with_suffix('.part')
        # No credentials or implicit HF login. Fail on access errors instead of asking for token output.
        url=f'https://huggingface.co/{REPO}/resolve/{REVISION}/{model.name}'
        with urllib.request.urlopen(url,timeout=120) as response, partial.open('wb') as target:
            shutil.copyfileobj(response,target,length=8*1024*1024)
        partial.replace(model)
    digest=hashlib.sha256()
    with model.open('rb') as source:
        for chunk in iter(lambda:source.read(8*1024*1024),b''): digest.update(chunk)
    if digest.hexdigest()!=expected: raise RuntimeError('GGUF checksum mismatch; inference blocked')
    for name in ['LICENSE','LICENSE-NVIDIA','NOTICE']:
        with urllib.request.urlopen(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{name}',timeout=30) as response:
            (folder/name).write_bytes(response.read())
    return model

def server_args(binary,model,hardware,layers=None):
    gpu_count=len(hardware['gpu_free_mib'])
    if layers is None: layers=99 if gpu_count>=2 else 30 if gpu_count else 0
    args=[str(binary),'-m',str(model),'-c','2048','-np','1','-b','128','-ub','64','-ngl',str(layers),
          '--host','127.0.0.1','--port','8001','--alias','driveos-evon-gguf','--jinja',
          '--chat-template-kwargs','{"enable_thinking":false}','--no-webui']
    if gpu_count>=2: args+=['--split-mode','layer','--tensor-split',','.join('1' for _ in range(gpu_count))]
    return args

def request_json(path,payload=None,timeout=180):
    headers={'Content-Type':'application/json'}
    if os.getenv('LLAMA_API_KEY'): headers['Authorization']='Bearer '+os.environ['LLAMA_API_KEY']
    request=urllib.request.Request('http://127.0.0.1:8001'+path,
        data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
    with urllib.request.urlopen(request,timeout=timeout) as response: return json.load(response)

def correct_plan(value,language):
    if not isinstance(value,dict) or set(value)!={'goal','tasks','next_action','needs_confirmation'}: return False
    if not isinstance(value['goal'],str) or not 1<=len(value['goal'])<=300: return False
    if value['needs_confirmation'] is not False or value['next_action']!='contact.notify_delay': return False
    tasks=value['tasks']
    if not isinstance(tasks,list) or len(tasks)!=1: return False
    task=tasks[0]
    if not isinstance(task,dict) or set(task)!={'tool','contact','delay_minutes'}: return False
    if task['tool']!='contact.notify_delay' or task['contact']!='Ananya': return False
    if type(task['delay_minutes']) is not int or task['delay_minutes']!=25: return False
    return language!='kn-IN' or any('\u0c80'<=letter<='\u0cff' for letter in value['goal'])

def smoke(schema):
    results=[]
    for language,text in CASES:
        system=('Return a single JSON mission plan. Only tool: contact.notify_delay; synthetic contact: Ananya. '
                'Extract the requested delay in minutes. Set needs_confirmation=false. '
                'Write goal in the language/script of the user. Do not invent actions or show reasoning.')
        start=time.monotonic()
        response=request_json('/v1/chat/completions',{'model':'driveos-evon-gguf',
            'messages':[{'role':'system','content':system},{'role':'user','content':text}],
            'temperature':0,'top_p':0.95,'max_tokens':512,'stream':False,
            'chat_template_kwargs':{'enable_thinking':False},
            'response_format':{'type':'json_schema','schema':schema}})
        content=response['choices'][0]['message']['content']
        try: value=json.loads(content); correct=correct_plan(value,language)
        except (ValueError,TypeError): correct=False
        result={'language':language,'correct_plan':correct,'latency_seconds':round(time.monotonic()-start,2),
                'finish_reason':response['choices'][0].get('finish_reason'),'usage':response.get('usage'),
                'schema_constrained':True}
        results.append(result); print(json.dumps(result))
    return results

def stop(process):
    if process.poll() is None:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=10)

def experiment(schema, mission_schema, benchmark_cases):
    hardware=preflight();binary=build(hardware)
    reports=[]
    for quant in ['Q3_K_S','Q3_K_M','IQ4_XS']:
        # CPU-only fallback must fit in available RAM; partial GPU offload can divide memory.
        if not hardware['gpu_free_mib'] and hardware['ram_available_gib']<QUANTS[quant][0]+3:
            reports.append({'quant':quant,'status':'insufficient_memory'});continue
        if shutil.disk_usage(ROOT).free/2**30<QUANTS[quant][0]+3:
            reports.append({'quant':quant,'status':'insufficient_disk'});continue
        model=download(quant)
        configurations=[None,10] if hardware['gpu_free_mib'] else [0]
        for layers in configurations:
            log=ROOT/f'{quant}-{layers}.log'
            with log.open('w') as output:
                process=subprocess.Popen(server_args(binary,model,hardware,layers),stdout=output,stderr=output)
            try:
                deadline=time.monotonic()+300
                while time.monotonic()<deadline:
                    if process.poll() is not None: raise RuntimeError('llama-server failed to load; inspect local log')
                    try:
                        if request_json('/health',timeout=5).get('status')=='ok': break
                    except (OSError,ValueError): pass
                    time.sleep(2)
                else: raise RuntimeError('Model load timed out')
                results=smoke(schema)
                passed=all(item['correct_plan'] and item['finish_reason']!='length' for item in results)
                benchmark=planning_benchmark(mission_schema,benchmark_cases) if passed else []
                passed=passed and all(item['correct_plan'] for item in benchmark)
                reports.append({'quant':quant,'layers':layers,'passed':passed,'results':results,'planning_benchmark':benchmark})
                (ROOT/'smoke-results.json').write_text(json.dumps({'hardware':hardware,'runs':reports},indent=2))
                if passed:
                    print('Gates A-D passed (load, English, Kannada, expected plans). Loopback endpoint: http://127.0.0.1:8001/v1')
                    return process,reports
                break  # Semantic failure: test the next feasible quant rather than more layer settings.
            except (OSError,RuntimeError,ValueError,TypeError,KeyError,IndexError) as error:
                reports.append({'quant':quant,'layers':layers,'passed':False,'error_type':type(error).__name__})
            finally:
                if not (reports and reports[-1].get('passed')): stop(process)
        # Delete only our failed downloaded quant to avoid retaining multiple large artifacts.
        if model.parent.resolve()==(ROOT/'models').resolve(): model.unlink()
        (ROOT/'smoke-results.json').write_text(json.dumps({'hardware':hardware,'runs':reports},indent=2))
    (ROOT/'smoke-results.json').write_text(json.dumps({'hardware':hardware,'runs':reports},indent=2))
    raise RuntimeError('No tested quant passed. Results retained; do not expose an endpoint.')


def planning_benchmark(schema,cases):
    """Run only after both basic language cases pass. No tool execution or paid speech."""
    results=[]
    for case in cases:
        start=time.monotonic()
        request=case['input']
        system=('Return only JSON matching the supplied schema. Use only provided facts and tools. '
                'Calendar change depends on negotiation acceptance. Respect total detour limit. '
                'Fuel means selecting a route stop, not purchasing. No reasoning.')
        response=request_json('/v1/chat/completions',{'model':'driveos-evon-gguf',
            'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(request,ensure_ascii=False)}],
            'temperature':0,'top_p':0.95,'max_tokens':1024,'stream':False,
            'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_schema','schema':schema}})
        choice=response['choices'][0]
        correct=False
        try:
            value=json.loads(choice['message']['content'])
            expected=case['expected']
            nodes={task['id']:task for task in value['tasks']}
            actual={task['action']:{'arguments':task['arguments'],
                    'depends_on':sorted(nodes[key]['action'] for key in task['depends_on'])} for task in value['tasks']}
            correct=(set(value)=={'version','goal','tasks','needs_confirmation'} and value['version']=='1'
                     and value['needs_confirmation'] is False and isinstance(value['goal'],str) and 1<=len(value['goal'])<=300
                     and len(nodes)==len(value['tasks'])==len(actual) and actual==expected
                     and all(set(task)=={'id','action','arguments','depends_on'} for task in value['tasks'])
                     and choice.get('finish_reason')!='length')
        except (ValueError,KeyError,TypeError): pass
        result={'case':case['id'],'correct_plan':correct,'latency_seconds':round(time.monotonic()-start,2),
                'finish_reason':choice.get('finish_reason'),'usage':response.get('usage')}
        results.append(result);print(json.dumps(result))
    return results
