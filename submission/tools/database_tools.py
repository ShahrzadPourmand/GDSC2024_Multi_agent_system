from langchain_core.tools import tool
from sqlalchemy import text
from src.static.util import ENGINE
import re
from difflib import get_close_matches

TABLE_LIST = ["Students", "StudentQuestionnaireEntries", "StudentQuestionnaireAnswers",
              "SchoolQuestionnaireEntries", "SchoolQuestionnaireAnswers",
              "TeacherQuestionnaireEntries", "TeacherQuestionnaireAnswers",
              "HomeQuestionnaireEntries", "HomeQuestionnaireAnswers",
              "CurriculumQuestionnaireEntries", "CurriculumQuestionnaireAnswers",
              "Schools", "Teachers", "StudentTeachers", "Homes", "Curricula",
              "StudentScoreEntries", "StudentScoreResults", "Benchmarks",
              "Countries"]

Answers_list = ["StudentQuestionnaireAnswers", "SchoolQuestionnaireAnswers",
                "TeacherQuestionnaireAnswers", "HomeQuestionnaireAnswers", "CurriculumQuestionnaireAnswers"]

QUESTIONNAIRES_QTYPE = {
    "StudentQuestionnaireEntries": [
        "About you",
        "Your school",
        "Reading in school",
        "Bullying",
        "What you think about reading",
        "Reading outside of school",
        "Using the library"
    ],
    "SchoolQuestionnaireEntries": [
        "Instructional Time",
        "Reading in Your School",
        "School Emphasis on Academic Success",
        "School Enrollment and Characteristics",
        "Studentsâ€™ Literacy Readiness",
        "Principal Experience and Education",
        "COVID-19 Pandemic",
        "Resources and Technology",
        "School Discipline and Safety"
    ],
    "TeacherQuestionnaireEntries": [
        "About Being a Teacher",
        "School Emphasis on\r\nAcademic Success",
        "School Environment",
        "About Teaching Reading\r\nto the PIRLS Class",
        "Reading Homework",
        "Computer and Library Resources",
        "About You",
        "Assessing Reading"
    ],
    "HomeQuestionnaireEntries": [
        "COVID-19 Pandemic",
        "Your Childâ€™s School",
        "Beginning Primary/Elementary School",
        "Literacy in the Home",
        "Before Your Child Began Primary/Elementary School",
        "Additional Information"
    ],
    "CurriculumQuestionnaireEntries": [
        "Curriculum Specifications",
        "About the Fourth Grade Language/Reading Curriculum",
        "Principal Preparation",
        "Areas of Emphasis in the Language/Reading Curriculum",
        "Instructional Materials and Use of Digital Devices",
        "Teacher Preparation",
        "Grade Structure and Student Flow",
        "Languages of Instruction",
        "COVID-19 Pandemic",
        "Early Childhood Education"
    ]
}

@tool
def query_database(query: str) -> str:
    """Query the PIRLS postgres database and return the results as a string.

    Args:
        query (str): The SQL query to execute.

    Returns:
        str: The results of the query as a string, where each row is separated by a newline.

    Raises:
        Exception: If the query is invalid or encounters an exception during execution.
    """
    # lower_query = query.lower()
    # record_limiters = ['count', 'where', 'limit', 'distinct', 'having', 'group by']
    # if not any(word in lower_query for word in record_limiters):
    #     return 'WARNING! The query you are about to perform has no record limitations! In case of large tables and ' \
    #            'joins this will return an incomprehensible output.'

    with ENGINE.connect() as connection:
        try:
            res = connection.execute(text(query))
        except Exception as e:
            return f'Wrong query, encountered exception {e}.'

    max_result_len = 3_000
    ret = '\n'.join(", ".join(map(str, result)) for result in res)
    if len(ret) > max_result_len:
        ret = ret[:max_result_len] + '...\n(results too long. Output truncated.)'

    return f'Query: {query}\nResult: {ret}'


@tool('get_tables_from_database')
def get_tables_from_database() -> str:
    """
    Retrieves a list of table names from the public schema of the connected database.

    Returns:
        str: A string containing a list of table names, each on a new line in the format:
             (Table: table_name)
             If an error occurs during execution, it returns an error message instead.

    Raises:
        Exception: If there's an error executing the SQL query, the exception is caught
                   and returned as a string message.
    """

    query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    with ENGINE.connect() as connection:
        try:
            res = connection.execute(text(query))
        except Exception as e:
            return f'Wrong query, encountered exception {e}.'

    tables = []
    for table in res:
        table = re.findall(r'[a-zA-Z]+', str(table))[0]
        tables.append(f'(Table: {table})\n')
    return ''.join(tables)



@tool
def get_question_types(table_name: str) -> str:
    """
    Retrives the type of questions available in a questionnaire table.
    Args:
        table_name(str) : The name of the table, must be one of the following: "StudentQuestionnaireEntries", "SchoolQuestionnaireEntries",
                       "TeacherQuestionnaireEntries", "HomeQuestionnaireEntries", "CurriculumQuestionnaireEntries"
    Returns:
        str: A string containing the type of questions available in the questionnaire table.
             If an error occurs during execution, it returns an error message instead.
    """
    if table_name.lower() not in (key.lower() for key in QUESTIONNAIRES_QTYPE.keys()):
        return "Error: Wrong table name."
    query = "SELECT DISTINCT type FROM " + str(table_name)
    with ENGINE.connect() as connection:
        try:
            res = connection.execute(text(query))
        except Exception as e:
            return f'Wrong query, encountered exception {e}.'

    ret = '\n'.join(", ".join(map(str, result)) for result in res)
    #ret = '\n'.join(", ".join(str(value) for value in result) for result in res)
    return ret

@tool
def get_distinct_answers(table_name: str, code: str) -> str:
    """
    Retrives distinct answers of a question from QuestionnaireAnswers table.
    Args:
        table_name(str) : The name of the table, must be one of the following: "StudentQuestionnaireAnswers", "SchoolQuestionnaireAnswers",
                "TeacherQuestionnaireAnswers", "HomeQuestionnaireAnswers", "CurriculumQuestionnaireAnswers"
        code (str) : the code of the question. You can get the code from get_all_questions_of_type tool.
    Returns:
        str: A string containing distinct answers of a question from QuestionnaireAnswers table.
             If an error occurs during execution, it returns an error message instead.
    """
    if table_name.lower() not in [t.lower() for t in Answers_list]:
        return "Error: Wrong table name."
    query = "SELECT DISTINCT answer FROM "+str(table_name)+" WHERE code = '"+str(code)+"'"
    with ENGINE.connect() as connection:
        try:
            res = connection.execute(text(query))
        except Exception as e:
            return f'Wrong query, encountered exception {e}.'

    ret = '\n'.join(", ".join(map(str, result)) for result in res)
    return ret


@tool
def get_all_questions_of_type(table_name: str, question_type: str) -> str:
    """
    Retrives all the questions of a specific type and their code from questionnaire table.
    Args:
        table_name(str) : The name of the table, must be one of the following: "StudentQuestionnaireEntries", "SchoolQuestionnaireEntries",
                       "TeacherQuestionnaireEntries", "HomeQuestionnaireEntries", "CurriculumQuestionnaireEntries"
        question_type(str) : The type of the question that is available in that table. You can get the list of available types from get_question_types tool.
    Returns:
        str: A string containing the type of questions available in the questionnaire table with their corresponding code.
             If an error occurs during execution, it returns an error message instead.
    """
    original_table = None
    for key in QUESTIONNAIRES_QTYPE.keys():
        if key.lower() == table_name.lower():
            original_table = key
            break

    if original_table is None:
        return "Error: Wrong table name."
    # Get the list of valid types for the specified table
    valid_types = QUESTIONNAIRES_QTYPE[original_table]

    # Check if the user-provided type exists in the valid types for that table
    if question_type not in valid_types:
        # Find the closest match within the table's valid types
        closest_match = get_close_matches(question_type, valid_types, n=1, cutoff=0.6)
        if closest_match:
            question_type = closest_match[0]  # Use the closest match
        else:
            return "Type not found."
    
    query = "SELECT DISTINCT question, code FROM " + str(table_name) + " WHERE type = '" + question_type + "'"
    with ENGINE.connect() as connection:
        try:
            res = connection.execute(text(query))
        except Exception as e:
            return f'Wrong query, encountered exception {e}.'

    ret = '\n'.join(", ".join(map(str, result)) for result in res)
    return ret


@tool
def get_all_countries() -> str:
    """
    Retrieves the columns country_id, name, benchmark, and test_type from the countries table.
    Note that some countries may appear in multiple rows.
    Returns:
        str: A string containing the country_id, name, benchmark, test_type columns from countries table.
             If an error occurs during execution, it returns an error message instead.
    """
    query = "SELECT country_id, name, benchmark, testtype FROM countries"
    with ENGINE.connect() as connection:
        try:
            res = connection.execute(text(query))
        except Exception as e:
            return f'Wrong query, encountered exception {e}.'

    ret = '\n'.join(", ".join(map(str, result)) for result in res)
    return ret


@tool
def get_info_about_table(table_name: str) -> str:
    """Returns the schema and explenation about a specific table, from PIRLS dataset.

    Args:
        table_name (str): The name of the table

    Returns:
        str: The information about that table or an error message.
    """

    if table_name.lower() == "students":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Student_ID: Int (Primary Key) - uniquely identifies student,\n"
            "Country_ID: Int (Foreign Key) - uniquely identifies student's country,\n"
            "School_ID: Int (Foreign Key) - uniquely identifies student's school,\n"
            "Home_ID: Int (Foreign Key) - uniquely identifies student's home"
        )
        return table_info
    elif table_name.lower() in (key.lower() for key in QUESTIONNAIRES_QTYPE.keys()):
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Code: String (Primary Key) - uniquely identifies a question,\n"
            "Question: String - the question,\n"
            "Type: String - describes the type of the question.\n"
            "Entries tables contain questions themselves and Answers tables contain answers to those question. \n"
            "For example StudentQuestionnaireEntries table contains questions asked in the students' questionnaire and StudentQuestionnaireAnswers table contains"                 "answers to those question."
            "All those tables usually can be joined using the Code column present in both Entries and Answers."
        )
        return table_info
    elif table_name.lower() in [t.lower() for t in Answers_list]:
        Id_name = table_name.lower().replace("questionnaireanswers", "")
        table_info = (
            "Schema of the "+table_name+" table:\n"
            + Id_name +"_ID: Int (Foreign Key) - references "+ Id_name +" from " + Id_name + " table\n"
            "Code: String (Foreign Key) - references question code from "+ Id_name +"QuestionnaireEntries table,\n"
            "Answer: String - contains the answer to the question\n"
        )
        return table_info
    elif table_name.lower() == "schools":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "School_ID: Int (Primary Key) - uniquely identifies a School,\n"
            "Country_ID: Int (Foreign Key) - uniquely identifies a country\n"
        )
        return table_info
    elif table_name.lower() == "teachers":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Teacher_ID: Int (Primary Key) - uniquely identifies a Teacher,\n"
            "School_ID: Int (Foreign Key) - uniquely identifies a School.\n"
        )
        return table_info
    elif table_name.lower() == "studentteachers":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Teacher_ID: Int (Foreign Key),\n"
            "Student_ID: Int (Foreign Key)\n"
        )
        return table_info
    elif table_name.lower() == "homes":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Home_ID: Int (Primary Key) - uniquely identifies a Home\n"
        )
        return table_info
    elif table_name.lower() == "curricula":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Curriculum_ID: Int (Primary Key),\n"
            "Country_ID: Int (Foreign Key)\n"
        )
        return table_info
    elif table_name.lower() == "studentscoreentries":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Code: String (Primary Key),\n"
            "Name: String,\n"
            "Type: String.\n"
            "\n"
            "In the student evaluation process 5 distinct scores were measured. The measured codes in StudentScoreEntries are:\n"
            "- ASRREA_avg and ASRREA_std describe the overall reading score average and standard deviation\n"
            "- ASRLIT_avg and ASRLIT_std describe literary experience score average and standard deviation\n"
            "- ASRINF_avg and ASRINF_std describe the score average and standard deviation in acquiring and information usage\n"
            "- ASRIIE_avg and ASRIIE_std describe the score average and standard deviation in interpreting, integrating and evaluating\n"
            "- ASRRSI_avg and ASRRSI_avg describe the score average and standard deviation in retrieving and straightforward inferencing\n"
        )
        return table_info
    elif table_name.lower() == "studentscoreresults":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Student_ID: Int (Foreign Key) - references student from Students table,\n"
            "Code: String (Foreign Key) - references score code from StudentScoreEntries table.\n"
            "Score: Float - the numeric score for a student.\n"
        )
        return table_info
    elif table_name.lower() == "benchmarks":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Benchmark_ID: Int (Primary Key) - uniquely identifies benchmark,\n"
            "Score: Int - the lower bound of the benchmark. Students that are equal to or above this value are of that category,\n"
            "Name: String - name of the category. Possible values are: Intermediate International Benchmark,Low International Benchmark, High International Benchmark, Advanced International Benchmark\n"
            "Benchmarks table cannot be joined with any other table but it keeps useful information about how to interpret student score as one of the 4 categories.\n"
        )
        return table_info
    elif table_name.lower() == "countries":
        table_info = (
            "Schema of the "+table_name+" table:\n"
            "Country_ID: Int (Primary Key) - uniquely identifies a country,\n"
            "Name: String - full name of the country,\n"
            "Code: String - 3 letter code of the country,\n"
            "Benchmark: Boolean - boolean value saying if the country was a benchmark country.\n"
            "TestType: String - describes the type of test taken in this country. It's either digital or paper.\n"
        )
        return table_info
    return "Table information not available"
