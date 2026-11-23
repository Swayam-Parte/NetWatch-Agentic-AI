from agents.base import BaseAgent
from memory.case_memory import find_similar_cases
from config import settings
class MemoryAgent(BaseAgent):
    name = "Memory Agent"
    def run(self, ctx):
        ctx.log(self.name,"started","Retrieving similar historical cases.")
        query = f"{ctx.state.get('issue','')} {ctx.state.get('diagnosis','')}"
        cases = find_similar_cases(query, top_k=2, threshold=settings.memory_similarity_threshold)
        ctx.state['similar_cases'] = cases
        ctx.log(self.name,"completed",{"matches":len(cases)})
        return cases
