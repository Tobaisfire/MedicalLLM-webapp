from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import uuid
import os
import re
import time
import logging
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import threading
# from langchain.llms import OpenAI  # If needed for compatibility

from dotenv import load_dotenv

# Load the .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")






client = QdrantClient(url="http://localhost:6333")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en") 


print("Embedding model loaded  : /n", embeddings)


collection_name = "Handbook_of_Clinical_Psychiatry"
collection_name2 ="Handbook_of_diagnostic_and_statistical_manual"

def VectosrStore(client,collection_name,embedding):
    return client,collection_name,embedding

vector_store_diag =VectosrStore(client,collection_name2,embeddings)
vector_store_drug = VectosrStore(client,collection_name,embeddings)
vector_store_treatment = VectosrStore(client,collection_name,embeddings)

# LLM setup
llm = ChatOpenAI(model_name='gpt-4.1-nano',api_key=api_key)

print("LLM model loaded  : /n", llm)

# Retrieval function

def retrieve(query: str, vector_store):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store[0].query_points(
                collection_name="Handbook_of_Clinical_Psychiatry",
                query=embeddings.embed_query(query),
                with_payload=True,
                limit=6
                ).points

    serialized = []
    for doc in range(len(retrieved_docs)):
        serialized.append(f"Source {doc+1}: \n{retrieved_docs[doc].payload.get('metadata')}\n" f"Content{doc+1}: \n{retrieved_docs[doc].payload.get('Content')}")
    return "\n\n\n".join(serialized), retrieved_docs

# Agent classes
class DiagnosisAgent:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        self.tools = [retrieve]
    def run(self, query):
        tool_messages = self.tools[0](query, self.vector_store)
        system_message_content = (
            "You are an Diagnosis assistant your tasks is to provide deep diagnosis result. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Give detailed answer"
            "\n\n"
            f"Question : {query}"
            "\n\n"
            "Context : \n"
            f"{tool_messages}"
        )
        prompt = system_message_content
        response = self.llm.invoke(prompt)
        return {"Response": [response]}

class DrugAgent:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        self.tools = [retrieve]
    def run(self, query):
        tool_messages = self.tools[0](query, self.vector_store)
        system_message_content = (
            "You are an medical drug assistant your tasks is to provide coreect medicines. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Give medicine with explanantion and reason."
            "\n\n"
            f"Question : {query}"
            "\n\n"
            "Context : \n"
            f"{tool_messages}"
        )
        prompt = system_message_content
        response = self.llm.invoke(prompt)
        return {"Response": [response]}

class TreatmentAgent:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        self.tools = [retrieve]
    def run(self, query):
        tool_messages = self.tools[0](query, self.vector_store)
        system_message_content = (
            "You are an medical drug assistant your tasks is to provide treatment guidelines. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Provide medical treatment according to question and context understanding"
            "\n\n"
            f"Question : {query}"
            "\n\n"
            "Context : \n"
            f"{tool_messages}"
        )
        prompt = system_message_content
        response = self.llm.invoke(prompt)
        return {"Response": [response]}

# ArgumentativeFramework for debate, logging, and report generation
class ArgumentativeFramework:
    def __init__(self, diagnosis_agent, treatment_agent, medicine_agent, llm):
        self.diagnosis_agent = diagnosis_agent
        self.treatment_agent = treatment_agent
        self.medicine_agent = medicine_agent
        self.llm = llm
        self.execution_log = {
            "api_calls": [],
            "debate_rounds": []
        }
        self.debate_id = str(uuid.uuid4())[:8]
        self.output_dir = os.path.join(r'K:\medicllm(bot)\test', f"debate_session_{self.debate_id}")


    def log_api_call(self, agent_name, start_time, end_time, request_content, response_content):
        call_details = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "duration_sec": end_time - start_time,
            "request_size": len(str(request_content)),
            "response_size": len(str(response_content)),
        }
        self.execution_log["api_calls"].append(call_details)
        return call_details

    def create_debate_prompt(self, patient_info, diagnosis_output, treatment_output, medicine_output, debate_history):
        prompt_template = PromptTemplate(
            input_variables=["patient_info", "diagnosis_output", "treatment_output", "medicine_output", "debate_history"],
            template="""
              You are a sophisticated medical reasoning system that synthesizes responses from multiple medical specialists.

              Patient Information:
              {patient_info}

              DiagnosisAgent says:
              {diagnosis_output}

              TreatmentAgent says:
              {treatment_output}

              MedicineAgent says:
              {medicine_output}

              Previous Debate (if any):
              {debate_history}

              Start a rigorous and structured medical debate:
              1. Analyze the quality, consistency, and evidence base of each agent's response
              2. Identify and challenge weak points, contradictions, or incomplete reasoning
              3. Highlight strong evidence and sound medical reasoning
              4. Explicitly acknowledge uncertainties or areas where more information is needed
              5. Consider potential risks and benefits of proposed treatments
              6. Assess medication interactions based on the patient's history and current medications
              7. Propose the most clinically supported diagnosis and treatment plan

              In your analysis, use medical criteria such as:
              - Alignment with established clinical guidelines
              - Consideration of patient-specific factors (age, comorbidities, etc.)
              - Evidence-based reasoning
              - Risk-benefit assessment
              - Consideration of alternatives

              Your output must follow this structure using Markdown formatting:
              # Medical Debate Analysis

              ## Debate Summary
              [Comprehensive analysis of the three perspectives]

              ## Points of Agreement
              [List key areas where the specialists align]

              ## Points of Contention
              [List key areas where the specialists disagree and analyze each perspective]

              ## Evidence Assessment
              [Evaluate the quality of evidence presented by each specialist]

              ## Final Recommendation
              ### Diagnosis
              [Most supported diagnosis with confidence level]

              ### Treatment Plan
              [Comprehensive treatment approach]

              ### Medications
              [Complete medication regimen with dosages and durations]

              ### Precautions and Follow-up
              [Risk mitigation and monitoring plan]
              """
        )
        return prompt_template

    def run_argumentation(self, patient_info, rounds=1,output_dir=None):
        start_time = time.time()
        # Step 1: Get raw outputs from agents
        diag_start = time.time()
        diagnosis_response = self.diagnosis_agent.run(patient_info)
        diag_end = time.time()
        print(self.log_api_call("DiagnosisAgent", diag_start, diag_end, patient_info, diagnosis_response))
        time.sleep(5)
        treat_start = time.time()
        treatment_response = self.treatment_agent.run(patient_info)
        treat_end = time.time()
        print(self.log_api_call("TreatmentAgent", treat_start, treat_end, patient_info, treatment_response))
        time.sleep(5)
        med_start = time.time()
        medicine_response = self.medicine_agent.run(patient_info)
        med_end = time.time()
        print(self.log_api_call("MedicineAgent", med_start, med_end, patient_info, medicine_response))
        time.sleep(1)
        debate_history = ""
        all_debates = []
        diagnosis_content = diagnosis_response['Response'][0].content
        treatment_content = treatment_response['Response'][0].content
        medicine_content = medicine_response['Response'][0].content
        self.save_agent_responses({
            "diagnosis": diagnosis_content,
            "treatment": treatment_content,
            "medicine": medicine_content
        },output_dir)
        for round_num in range(rounds):
            prompt = self.create_debate_prompt(
                patient_info,
                diagnosis_content,
                treatment_content,
                medicine_content,
                debate_history
            )
            debate_start = time.time()
            chain = LLMChain(llm=self.llm, prompt=prompt)
            debate_input = {
                "patient_info": patient_info,
                "diagnosis_output": diagnosis_content,
                "treatment_output": treatment_content,
                "medicine_output": medicine_content,
                "debate_history": debate_history
            }
            debate_result = chain.run(debate_input)
            time.sleep(1)
            debate_end = time.time()
            self.log_api_call("DebateChain", debate_start, debate_end, debate_input, debate_result)
            print(self.log_api_call("DebateChain", debate_start, debate_end, debate_input, debate_result))
            debate_round = {
                "round": round_num + 1,
                "timestamp": datetime.now().isoformat(),
                "debate_result": debate_result,
                "duration_sec": debate_end - debate_start
            }
            self.execution_log["debate_rounds"].append(debate_round)
            print(self.execution_log["debate_rounds"])
            all_debates.append(debate_result)
            debate_history = debate_result
        final_recommendation = self.extract_final_recommendation(debate_result)
        end_time = time.time()
        return {
            "debate_id": self.debate_id,
            "patient_info": patient_info,
            "agent_responses": {
                "diagnosis": diagnosis_content,
                "treatment": treatment_content,
                "medicine": medicine_content
            },
            "debate_rounds": all_debates,
            "final_debate": debate_result,
            "final_recommendation": final_recommendation,
            "execution_log": self.execution_log,
            "total_duration": end_time - start_time,
            "output_dir": self.output_dir
        }
    def extract_final_recommendation(self, debate_result):
        pattern = r"## Final Recommendation(.*?)(?=\n#|\Z)"
        match = re.search(pattern, debate_result, re.DOTALL)
        if not match:
            return "No clear recommendation found."
        return match.group(1).strip()
    def save_agent_responses(self, responses,output_dir):
        for agent, content in responses.items():
            filename = os.path.join(output_dir, f"{agent}_response.md")
            with open(filename, "w") as f:
                f.write(f"# {agent.capitalize()} Agent Response\n\n")
                f.write(content)
    def generate_timing_chart(self,output_dir):
        if not self.execution_log["api_calls"]:
            return None
        df = pd.DataFrame(self.execution_log["api_calls"])
        plt.figure(figsize=(10, 6))
        sns.barplot(x="agent", y="duration_sec", data=df)
        plt.title("API Call Duration by Agent")
        plt.xlabel("Agent")
        plt.ylabel("Duration (seconds)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        output_path = os.path.join(output_dir, "api_timing_chart.png")
        plt.savefig(output_path)
        return output_path
    
    def generate_response_comparison(self, debate_result):
        """Generate a visual comparison of agent responses."""
        # Calculate response lengths
        agent_names = list(debate_result["agent_responses"].keys())
        response_lengths = [len(debate_result["agent_responses"][agent]) for agent in agent_names]
        
        # Count entities in each response
        entity_counts = []
        for agent, response in debate_result["agent_responses"].items():
            # Simple count of medical terms
            count = sum(1 for term in ['diagnosis', 'treatment', 'medication', 'symptom', 'patient', 
                                       'disease', 'disorder', 'therapy', 'dose', 'drug'] 
                          if term in response.lower())
            entity_counts.append(count)
        
        # Create a DataFrame for visualization
        df = pd.DataFrame({
            'Agent': agent_names,
            'Response Length': response_lengths,
            'Medical Terms': entity_counts
        })
        
        # Create plot with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Response length bar chart
        sns.barplot(x='Agent', y='Response Length', data=df, ax=ax1)
        ax1.set_title('Response Length by Agent')
        ax1.set_ylabel('Character Count')
        
        # Medical terms bar chart
        sns.barplot(x='Agent', y='Medical Terms', data=df, ax=ax2)
        ax2.set_title('Medical Term Count by Agent')
        ax2.set_ylabel('Count')
        
        plt.tight_layout()
        output_path = os.path.join(debate_result["output_dir"], "response_comparison.png")
        plt.savefig(output_path)
        plt.close()
        return output_path
    
    def save_debate_log(self, debate_result):
        log_filename = os.path.join(debate_result["output_dir"], "debate_log.md")
        with open(log_filename, "w") as f:
            f.write(f"# Medical Debate Log\n\n")
            f.write(f"## Session Information\n")
            f.write(f"- **Debate ID**: {debate_result['debate_id']}\n")
            f.write(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Total Duration**: {debate_result['total_duration']:.2f} seconds\n\n")
            f.write("## Patient Information\n")
            f.write("```\n" + debate_result["patient_info"].strip() + "\n```\n\n")
            f.write("## Initial Agent Responses\n\n")
            f.write("### Diagnosis Agent\n")
            f.write("```\n" + debate_result["agent_responses"]["diagnosis"].strip() + "\n```\n\n")
            f.write("### Treatment Agent\n")
            f.write("```\n" + debate_result["agent_responses"]["treatment"].strip() + "\n```\n\n")
            f.write("### Medicine Agent\n")
            f.write("```\n" + debate_result["agent_responses"]["medicine"].strip() + "\n```\n\n")
            f.write("## Debate Rounds\n\n")
            for i, debate in enumerate(debate_result["debate_rounds"]):
                f.write(f"### Round {i+1}\n\n")
                f.write(debate + "\n\n")
            f.write("## API Call Statistics\n\n")
            f.write("| Agent | Duration (seconds) | Timestamp |\n")
            f.write("|-------|-------------------|----------|\n")
            for call in debate_result["execution_log"]["api_calls"]:
                f.write(f"| {call['agent']} | {call['duration_sec']:.2f}s | {call['timestamp']} |\n")
            f.write(f"\n**Total duration**: {debate_result['total_duration']:.2f}s\n")
            f.write("\n## Visualizations\n\n")
            f.write("### API Timing Chart\n")
            f.write("![API Timing Chart](api_timing_chart.png)\n\n")
            f.write("### Response Comparison\n")
            f.write("![Response Comparison](response_comparison.png)\n\n")
            f.write("### Debate Graph\n")
            f.write("![Debate Graph](debate_graph.png)\n\n")
        return log_filename
        
    def generate_debate_graph(self, debate_result):
        G = nx.DiGraph()
        G.add_node("Patient", pos=(0, 0), node_type="input", content=debate_result["patient_info"][:100] + "...")
        G.add_node("Diagnosis", pos=(-1, -1), node_type="agent", content=self._extract_key_points(debate_result["agent_responses"]["diagnosis"]))
        G.add_node("Treatment", pos=(0, -1), node_type="agent", content=self._extract_key_points(debate_result["agent_responses"]["treatment"]))
        G.add_node("Medicine", pos=(1, -1), node_type="agent", content=self._extract_key_points(debate_result["agent_responses"]["medicine"]))
        for i, debate in enumerate(debate_result["debate_rounds"]):
            round_name = f"Round {i+1}"
            G.add_node(round_name, pos=(0, -2-i), node_type="debate", content=self._extract_key_points(debate))
            G.add_edge("Diagnosis", round_name)
            G.add_edge("Treatment", round_name)
            G.add_edge("Medicine", round_name)
            if i == 0:
                G.add_edge("Patient", "Diagnosis")
                G.add_edge("Patient", "Treatment")
                G.add_edge("Patient", "Medicine")
            else:
                G.add_edge(f"Round {i}", round_name)
        pos = nx.spring_layout(G, seed=42)
        plt.figure(figsize=(10, 8))
        node_colors = []
        for node in G.nodes(data=True):
            if node[1]["node_type"] == "input":
                node_colors.append("#FFD700")
            elif node[1]["node_type"] == "agent":
                node_colors.append("#87CEEB")
            else:
                node_colors.append("#FFB6C1")
        nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=2000, font_size=10, font_weight='bold', arrows=True)
        labels = {n: d["content"] for n, d in G.nodes(data=True)}
        for key, value in labels.items():
            x, y = pos[key]
            plt.text(x, y-0.1, value, fontsize=8, ha='center', va='center', wrap=True)
        output_path = os.path.join(debate_result["output_dir"], "debate_graph.png")
        plt.savefig(output_path)
        plt.close()
        return output_path
        
    def _extract_key_points(self, text, max_len=50):
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < max_len and ('diagnos' in line.lower() or 'recommend' in line.lower()):
                return line
        for line in lines:
            if len(line.strip()) > 10:
                return line.strip()[:max_len] + "..."
        return text[:max_len] + "..." if len(text) > max_len else text

# MedicalAssistant orchestration
class MedicalAssistant:
    def __init__(self, diagnosis_agent, treatment_agent, medicine_agent, llm):
        self.argumentative_framework = ArgumentativeFramework(diagnosis_agent, treatment_agent, medicine_agent, llm)
    
    def process_patient(self, patient_info, debate_rounds=2, output_dir=None):
        """Process a patient case with all agents and generate a final report."""
        # Use provided output_dir or create a default one
        if not output_dir:
            # Generate a unique ID for the debate session
            debate_id = str(uuid.uuid4())[:8]
            # Use the custom debate directory instead of creating at root level
            output_dir = os.path.join(r'K:\medicllm(bot)\test', f"debate_session_{debate_id}")
            os.makedirs(output_dir, exist_ok=True)
        
        # Run the argumentation process
        print("-------------------------------------------- Logic started -----------------------------------------------------")
        debate_result = self.argumentative_framework.run_argumentation(patient_info, rounds=debate_rounds,output_dir=output_dir)
        debate_result["output_dir"] = output_dir
        
        # Generate visualizations
        self.argumentative_framework.generate_timing_chart(output_dir=debate_result["output_dir"])
        self.argumentative_framework.generate_response_comparison(debate_result)
        self.argumentative_framework.save_debate_log(debate_result)
        self.argumentative_framework.generate_debate_graph(debate_result)
        
        # Generate the final recommendation report
        final_recommendation = self.generate_report(debate_result)
        debate_result["final_recommendation"] = final_recommendation
        
        return debate_result
    
    def generate_report(self, debate_result):
        """Generate a final report from the debate results."""
        pattern_diagnosis = r"### Diagnosis(.*?)(?=###|\Z)"
        pattern_treatment = r"### Treatment Plan(.*?)(?=###|\Z)"
        pattern_medications = r"### Medications(.*?)(?=###|\Z)"
        pattern_followup = r"### Precautions and Follow-up(.*?)(?=###|\Z)"
        diagnosis = self._extract_with_pattern(pattern_diagnosis, debate_result["final_debate"])
        treatment = self._extract_with_pattern(pattern_treatment, debate_result["final_debate"])
        medications = self._extract_with_pattern(pattern_medications, debate_result["final_debate"])
        followup = self._extract_with_pattern(pattern_followup, debate_result["final_debate"])
        report = f"""# Patient Medical Report\n\n## Report Information\n- **Case ID**: {debate_result["debate_id"]}\n- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n- **Processing Time**: {debate_result["total_duration"]:.2f} seconds\n- **Debate Rounds**: {len(debate_result["debate_rounds"])}\n\n## Patient Information\n{debate_result["patient_info"]}\n\n## Diagnosis\n{diagnosis}\n\n## Treatment Plan\n{treatment}\n\n## Medications\n{medications}\n\n## Precautions and Follow-up\n{followup}\n\n## Debate Analysis\nThe final recommendations were reached after analyzing inputs from three specialized medical agents and conducting {len(debate_result["debate_rounds"])} rounds of structured debate.\n\n### Agent Performance\n![API Timing Chart](api_timing_chart.png)\n\n### Response Comparison\n![Response Comparison](response_comparison.png)\n\n### Detailed Debate Flow\n![Debate Graph](debate_graph.png)\n\n## Conclusion\nThis medical case was processed using an argumentative AI framework that combines multiple expert perspectives to reach a clinically sound conclusion.\n"""
        report_filename = os.path.join(debate_result["output_dir"], "patient_report.md")
        with open(report_filename, "w") as f:
            f.write(report)
        return report
    def _extract_with_pattern(self, pattern, text):
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else "Not specified"



# if __name__ == "__main__":
    
#     diag_agent = DiagnosisAgent(vector_store_diag, llm)
#     drug_agent = DrugAgent(vector_store_drug, llm)
#     treatment_agent = TreatmentAgent(vector_store_treatment, llm)
#     medical_assistant = MedicalAssistant(diag_agent, treatment_agent, drug_agent, llm)

#     medical_assistant.process_patient(pantient_info, debate_rounds=1)

#     final_text_response = medical_assistant.process_patient(pantient_info, debate_rounds=1)['final_recommendation']