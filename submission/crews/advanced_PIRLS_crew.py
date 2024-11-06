from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from src.static.submission import Submission
from src.static.util import PROJECT_ROOT
import src.submission.tools.database_tools as db_tools
import src.submission.tools.search_tools as search
import src.submission.tools.other_tools as other_tools


@CrewBase
class AdvancedPIRLSCrew(Submission):
    """Data Analysis Crew for the GDSC project."""
    # Load the files from the config directory
    agents_config = PROJECT_ROOT / 'submission' / 'config' / 'agents.yaml'
    tasks_config = PROJECT_ROOT / 'submission' / 'config' / 'tasks.yaml'

    def __init__(self, llm):
        self.llm = llm

    def run(self, prompt: str) -> str:
        return self.crew().kickoff(inputs={'user_question': prompt}).raw

    @agent
    def data_engineer(self) -> Agent:
        a = Agent(
            config=self.agents_config['data_engineer'],
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
        )
        return a

    @agent
    def research_analyst(self) -> Agent:
        a = Agent(
            config=self.agents_config['research_analyst'],
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            tools=[
                #search.scrape_tool,
                search.get_PIRLS_tables
            ]
        )
        return a

    @agent
    def lead_data_analyst(self) -> Agent:
        a = Agent(
            config=self.agents_config['lead_data_analyst'],
            llm=self.llm,
            allow_delegation=False,
            verbose=True,
            tools=[
                other_tools.generate_chart,
                other_tools.generate_pie_chart
            ]
        )
        return a

    #@agent
    #def data_journalist(self) -> Agent:
    #    a = Agent(
    #        config=self.agents_config['data_journalist'],
    #        llm=self.llm,
    #        allow_delegation=False,
    #        verbose=True
    #    )
    #    return a

    @task
    def select_relevant_tables_task(self) -> Task:
        t = Task(
            config=self.tasks_config['select_relevant_tables_task'],
            agent=self.data_engineer(),
            #async_execution=True,
            tools=[
                db_tools.get_tables_from_database,
                db_tools.get_info_about_table,
                db_tools.get_question_types
            ]
        )
        return t

    @task
    def select_relevant_column_values(self) -> Task:
        t = Task(
            config=self.tasks_config['select_relevant_column_values'],
            agent=self.data_engineer(),
            context=[
                self.select_relevant_tables_task()
            ],
            tools=[
                #db_tools.get_tables_from_database, #
                db_tools.get_all_countries,
                db_tools.get_info_about_table,
                db_tools.get_question_types,
                db_tools.get_all_questions_of_type,
                db_tools.get_distinct_answers
            ]
        )
        return t

    @task
    def decompose_question_task(self) -> Task:
        t = Task(
            config=self.tasks_config['decompose_question_task'],
            agent=self.data_engineer(),
            context=[
                self.select_relevant_tables_task(),
                self.select_relevant_column_values()
            ],
            #tools=[
                #db_tools.get_info_about_table,
                #db_tools.get_tables_from_database
            #]
        )
        return t

    @task
    def refine_sql_task(self) -> Task:
        t = Task(
            config=self.tasks_config['refine_sql_task'],
            agent=self.data_engineer(),
            tools=[
                db_tools.query_database,
                db_tools.get_info_about_table
            ],
            context=[
                #self.select_relevant_tables_task(),
                self.select_relevant_column_values(),
                self.decompose_question_task()
            ]
        )
        return t

    @task
    def search_online_task(self) -> Task:
        t = Task(
            config=self.tasks_config['search_online_task'],
            agent=self.research_analyst(),
            #async_execution=True
        )
        return t

    @task
    def analyze_and_answer_question_task(self) -> Task:
        t = Task(
            config=self.tasks_config['analyze_and_answer_question_task'],
            context=[self.search_online_task(), self.refine_sql_task()],
            agent=self.lead_data_analyst()
        )
        return t

    #@task
    #def review_task(self) -> Task:
    #    t = Task(
    #        config=self.tasks_config['review_task'],
    #        context=[self.analyze_and_answer_question_task()],
    #        agent=self.data_journalist()
    #    )
    #    return t


    @crew
    def crew(self) -> Crew:
        """Creates the data analyst crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_iter=5,
            cache=True
        )
