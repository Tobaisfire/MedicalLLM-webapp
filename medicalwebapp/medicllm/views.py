from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse, FileResponse, Http404

import json
from .logic import *
import os
from .models import ChatSession, Message
from django.views.decorators.http import require_http_methods
import markdown2
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import re
import matplotlib.pyplot as plt
import networkx as nx
from IPython.display import display, HTML
from rapidfuzz import fuzz



# --------------------------
# Helper Function for Color Mapping for Bar Chart
# --------------------------
def get_bar_color(score):
    if score >= 0.5:
        return "#800000"  # Very dark red
    elif score >= 0.4:
        return "#A52A2A"  # Brownish red
    elif score >= 0.3:
        return "#CC3700"  # Bright Red-Orange
    elif score >= 0.25:
        return "#B22222"  # Firebrick Red
    elif score >= 0.2:
        return "#FF8C00"  # Dark Orange
    elif score >= 0.15:
        return "#FFD700"  # Gold
    elif score >= 0.1:
        return "#32CD32"  # Lime Green
    else:
        return "#1E90FF"  # Dodger Blue


def plot_explanation_graph_side_by_side(scores, disease,save_path):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor="none")
    G = nx.DiGraph()
    G.add_node(disease, color='yellow', size=2000)
    for symptom, weight in scores.items():
        G.add_node(symptom, color='cyan', size=1000)
        G.add_edge(symptom, disease, weight=weight)
    node_colors = [G.nodes[node]['color'] for node in G.nodes]
    node_sizes  = [G.nodes[node]['size'] for node in G.nodes]
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=node_sizes,
            edge_color='gray', font_size=10, font_weight='bold', ax=axes[0])
    axes[0].set_title("Symptoms to Disease Explanation Graph")
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    bar_features, bar_scores = zip(*sorted_items)
    bar_colors = [get_bar_color(s) for s in bar_scores]
    bars = axes[1].barh(bar_features, bar_scores, color=bar_colors, edgecolor='black')
    for bar, score in zip(bars, bar_scores):
        axes[1].text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                     f"{score*100:.1f}%",
                     va="center", ha="left", fontsize=12, color="black", fontweight="bold")
    axes[1].invert_yaxis()
    axes[1].set_title("Feature Scores Visualization")
    axes[1].set_xlabel("Score")
    axes[1].xaxis.set_visible(False)
    for ax in axes:
        for spine in ax.spines.values():
            spine.set_visible(False)
    plt.tight_layout()
    fig.savefig(save_path+"/xai_explanation.png", dpi=500, bbox_inches='tight') 
    return plt



# Create your views here.
def index(request):
    return render(request, "index.html")
@csrf_exempt
def process_patient_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            patient_info = data.get('patient_info', '')
            chat_id = data.get('chat_id', None)
            diag_agent = DiagnosisAgent(vector_store_diag, llm)
            drug_agent = DrugAgent(vector_store_drug, llm)
            treatment_agent = TreatmentAgent(vector_store_treatment, llm)
            medical_assistant = MedicalAssistant(diag_agent, treatment_agent, drug_agent, llm)

            # Patch: set output_dir to test/cases/<chat_id>/debate_session_<debate_id>
            output_dir = None
            if chat_id:
                base_dir = os.path.join('test', 'cases', chat_id)
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir, exist_ok=True)
                output_dir = base_dir  # MedicalAssistant will append debate_session_<debate_id>

            result = medical_assistant.process_patient(patient_info, debate_rounds=1, output_dir=output_dir)



            return JsonResponse({'final_recommendation': result.get('final_recommendation', 'No recommendation found.')})
        except Exception as e:
            return JsonResponse({'final_recommendation': f'Error: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
def chats_api(request):
    if request.method == 'GET':
        chats = ChatSession.objects.all().order_by('-created_at')
        data = []
        for chat in chats:
            messages = Message.objects.filter(chat=chat).order_by('timestamp')
            data.append({
                'id': chat.id,
                'title': chat.title,
                'created_at': chat.created_at.isoformat(),
                'messages': [
                    {'role': m.role, 'content': m.content, 'timestamp': m.timestamp.isoformat()} for m in messages
                ]
            })
        return JsonResponse({'chats': data})
    elif request.method == 'POST':
        body = json.loads(request.body)
        chat_id = body.get('id')
        title = body.get('title', '')
        chat, created = ChatSession.objects.get_or_create(id=chat_id)
        if title and chat.title != title:
            chat.title = title
            chat.save()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def messages_api(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        chat_id = body.get('chat_id')
        role = body.get('role')
        content = body.get('content')
        chat = ChatSession.objects.get(id=chat_id)
        Message.objects.create(chat=chat, role=role, content=content)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def view_patient_report(request, chat_id):
    # Find the latest patient_report.md in cases/<chat_id>/
    import glob, os
    print(chat_id)
    base_dir = os.path.join('test', 'cases', chat_id)
    print(base_dir)
    report_files = sorted(glob.glob(os.path.join(base_dir, 'patient_report.md')))
    print(report_files)
    if not report_files:
        return HttpResponse('No report found.', status=404)
    try:
        with open(report_files[-1], 'r', encoding='utf-8-sig') as f:
            md_content = f.read()
    except UnicodeDecodeError:
        with open(report_files[-1], 'r', encoding='latin-1') as f:
            md_content = f.read()
    html = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])
    return HttpResponse(f'<html><head><title>Patient Report</title></head><body style="font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;max-width:800px;margin:2em auto;">{html}</body></html>')




@csrf_exempt
def download_patient_report_pdf(request, chat_id):
    import glob, os
    base_dir = os.path.join('test', 'cases', chat_id)
    report_files = sorted(glob.glob(os.path.join(base_dir, 'patient_report.md')))
    if not report_files:
        return HttpResponse('No report found.', status=404)
    try:
        with open(report_files[-1], 'r', encoding='utf-8-sig') as f:
            md_content = f.read()
    except UnicodeDecodeError:
        with open(report_files[-1], 'r', encoding='latin-1') as f:
            md_content = f.read()
    # Convert markdown to plain text for PDF (or use a better renderer if needed)
    text_content = md_content.replace('#', '').replace('**', '').replace('`', '')
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    for line in text_content.split('\n'):
        if y < 40:
            p.showPage()
            y = height - 40
        p.drawString(40, y, line[:110])
        y -= 16
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'patient_report_{chat_id}.pdf')



@csrf_exempt
def view_saved_figure(request, chat_id):

    try:
        image_path = os.path.join('test', 'cases', chat_id, 'xai_explanation.png')

        print("\n\n Already XAI DONE.........")
        if not os.path.exists(image_path):
            raise Http404("Figure not found.")
    
        with open(image_path, 'rb') as f:
            return HttpResponse(f.read(), content_type="image/png")
        
    except:
        

        main_path = os.path.join('test', 'cases', chat_id)

        print("path : ", main_path)
        with open(main_path+"/patient_report.md","r") as fp:
            res = fp.read()

        # print(res)

        llm_response = res
        template = """
            Given the following get disease name and from context get the key symtopms from context and assign a weight score between 0 and 1 to each key symptopms based on its contribution to the disease.
            The sum of all assigned weights should be exactly 1.
            Key context:
            {context}
            Return the results in json with no extra content.
            """
        prompt = PromptTemplate(template=template, input_variables=["context"])
        chain = LLMChain(llm=llm, prompt=prompt)
        res = eval(chain.run(context=llm_response))

        print(res)

        dis_name = res[list(res.keys())[0]]
        res = res[list(res.keys())[1]]
        match = re.search(r"\{\s*[\s\S]*?\s*\}", str(res))
        if match:
            json_text = match.group(0)
            # print(json_text)
            try:
                scores_dict = eval(json_text)
            except json.JSONDecodeError as e:
                print("Error decoding JSON:", e)
                scores_dict = {}
        else:
            print("No valid JSON found!")
            scores_dict = {}
        total = sum(scores_dict.values())
        if total != 1:
            scores_dict = {key: round(value / total, 4) for key, value in scores_dict.items()}
        print("\n\n\n Socre :\n\n", scores_dict)
        extracted_disease = dis_name


        plot_explanation_graph_side_by_side(scores_dict, extracted_disease,main_path)



        if not os.path.exists(image_path):
            raise Http404("Figure not found.")

        with open(image_path, 'rb') as f:
            return HttpResponse(f.read(), content_type="image/png")