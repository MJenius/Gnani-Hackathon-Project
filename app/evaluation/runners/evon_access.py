"""Verify token/model access with metadata and HEAD requests; never download weights."""
import json
import os
from pathlib import Path
import httpx
from app import config

def main():
    token=os.getenv('HF_TOKEN')
    if not token: raise SystemExit('HF_TOKEN is not configured')
    model='gnani/gnani-evon-v3.3-30B-A3B'
    headers={'Authorization':'Bearer '+token}
    with httpx.Client(timeout=30,follow_redirects=True) as client:
        identity=client.get('https://huggingface.co/api/whoami-v2',headers=headers)
        if identity.status_code!=200: raise SystemExit(f'Hugging Face token validation HTTP {identity.status_code}')
        response=client.get('https://huggingface.co/api/models/'+model+'?expand[]=inferenceProviderMapping&expand[]=safetensors&expand[]=siblings',headers=headers)
        if response.status_code!=200: raise SystemExit(f'Model metadata HTTP {response.status_code}')
        metadata=response.json()
        weights=[item['rfilename'] for item in metadata.get('siblings',[]) if item['rfilename'].endswith('.safetensors')]
        status=None
        if weights:
            probe=client.head('https://huggingface.co/'+model+'/resolve/main/'+weights[0],headers=headers)
            status=probe.status_code
        parameters=metadata.get('safetensors',{}).get('total')
        result={'model':model,'token_valid':True,'weight_head_status':status,'weight_shards':len(weights),
                'parameters':parameters, 'bf16_weight_gb_estimate':round(parameters*2/1e9,1) if parameters else None,
                'inference_providers':list((metadata.get('inferenceProviderMapping') or {}).keys()),
                'weights_downloaded':False}
    output=Path('data/evon-access-results.json');output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if status!=200: raise SystemExit(1)

if __name__=='__main__': main()
