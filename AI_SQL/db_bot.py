import json
from openai import OpenAI
import os
import sqlite3
from time import time

print("Running db_bot.py!")

fdir = os.path.dirname(__file__)
def getPath(fname):
    return os.path.join(fdir, fname)

# SQLITE
sqliteDbPath = getPath("aidb.sqlite")
setupSqlPath = getPath("setup.sql")
setupSqlDataPath = getPath("setupData.sql")

# Erase previous db
if os.path.exists(sqliteDbPath):
    os.remove(sqliteDbPath)

# create new db
sqliteCon = sqlite3.connect(sqliteDbPath) 
sqliteCursor = sqliteCon.cursor()

# read in setup files
with (
        open(setupSqlPath) as setupSqlFile,
        open(setupSqlDataPath) as setupSqlDataFile
    ):

    setupSqlScript = setupSqlFile.read()
    setupSQlDataScript = setupSqlDataFile.read()

# execute setup files
sqliteCursor.executescript(setupSqlScript) # setup tables and keys
sqliteCursor.executescript(setupSQlDataScript) # setup tables and keys

def runSql(query):
    result = sqliteCursor.execute(query).fetchall()
    return result

# OPENAI
configPath = getPath("config.json")
print(configPath)
with open(configPath) as configFile:
    config = json.load(configFile)

openAiClient = OpenAI(api_key = config["openaiKey"])
openAiClient.models.list() # check if the key is valid (update in config.json)
chosen_model = "gpt-4o"

def getChatGptResponse(content):
    stream = openAiClient.chat.completions.create(
        model=chosen_model,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    return result


# strategies
commonSqlOnlyRequest = " Give me a sqlite select statement that answers the question. Only respond with sqlite syntax. If there is an error do not explain it!"
strategies = {
    "zero_shot": setupSqlScript + commonSqlOnlyRequest,
    "single_domain_double_shot": (setupSqlScript +
                   " Which fighter has the most total KOs, and on which stage was that fighter used most often? " +
                   " \nWITH fighter_totals AS (\n"
                   "    SELECT fighter_id, SUM(ko_count) AS total_kos\n"
                   "    FROM player_match\n"
                   "    GROUP BY fighter_id\n"
                   "), top_fighters AS (\n"
                   "    SELECT fighter_id\n"
                   "    FROM fighter_totals\n"
                   "    WHERE total_kos = (SELECT MAX(total_kos) FROM fighter_totals)\n"
                   "), stage_usage AS (\n"
                   "    SELECT pm.fighter_id, gm.stage_id, COUNT(*) AS usage_count\n"
                   "    FROM player_match pm\n"
                   "    JOIN game_match gm ON gm.match_id = pm.match_id\n"
                   "    WHERE pm.fighter_id IN (SELECT fighter_id FROM top_fighters)\n"
                   "    GROUP BY pm.fighter_id, gm.stage_id\n"
                   "), max_stage_usage AS (\n"
                   "    SELECT fighter_id, MAX(usage_count) AS max_usage\n"
                   "    FROM stage_usage\n"
                   "    GROUP BY fighter_id\n"
                   ")\n"
                   "SELECT f.fighter_name, s.stage_name, su.usage_count\n"
                   "FROM stage_usage su\n"
                   "JOIN max_stage_usage msu ON msu.fighter_id = su.fighter_id\n"
                   "    AND msu.max_usage = su.usage_count\n"
                   "JOIN fighter f ON f.fighter_id = su.fighter_id\n"
                   "JOIN stage s ON s.stage_id = su.stage_id;\n " +
                   commonSqlOnlyRequest)
     # TODO add strategies as descirbed in the paper (multi-domain)              
}

questions = [
    "Which player has won the most matches?",
    "Which fighter has the most wins?",
    "Which fighters have never been selected by a player?",
    "Which player has the most total KOs?",
    "How many matches has each player played?",
    "Which fighter has the best average ranking?",
    "Which stage has hosted the most matches?",
    "Which song has played in the most matches?",
    "Which game mode has been used for the most matches?",
    "Which items have appeared in the most matches?",
    "Who won each match, and which fighter did they use?",
    "What is the average number of KOs per match?",
    "Which match had the most total KOs?",
    "Which player has the most total KOs, which fighter did that player use most often, and on which stage did those matches take place most often?",
    "Which fighter has the most total KOs",
    "Which fighter has the most total KOs, and on which stage was that fighter used most often?"
]


# use the markdown for the sql syntax to find the SQL query
def sanitizeForJustSql(value):
    gptStartSqlMarker = "```"
    gptEndSqlMarker = "```"
    if gptStartSqlMarker in value:
        # Split at the first ``` and take everything after it
        value = value.split(gptStartSqlMarker, 1)[1]
        # Find the newline after the language identifier (sql, sqlite, etc.)
        newline_index = value.find("\n")
        if newline_index != -1:
            value = value[newline_index + 1:]
    if gptEndSqlMarker in value:
        # Split at the closing ``` and take everything before it
        value = value.split(gptEndSqlMarker, 1)[0]

    return value.strip()

for strategy in strategies:
    responses = {"strategy": strategy, "prompt_prefix": strategies[strategy]}
    questionResults = []
    print("########################################################################")
    print(f"Running strategy: {strategy}")
    for question in questions:

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Question:")
        print(question)
        error = "None"
        try:
            getSqlFromQuestionEngineeredPrompt = strategies[strategy] + " " + question
            sqlSyntaxResponse = getChatGptResponse(getSqlFromQuestionEngineeredPrompt)
            sqlSyntaxResponse = sanitizeForJustSql(sqlSyntaxResponse)
            print("SQL Syntax Response:")
            print(sqlSyntaxResponse)
            queryRawResponse = str(runSql(sqlSyntaxResponse))
            print("Query Raw Response:")
            print(queryRawResponse)

            # TODO this prompt is insufficient. ChatGPT doesn't have all the context that it needs.
            # What context would help the friendly response be more successful? Can you fix it?
            friendlyResultsPrompt = "I asked a question \"" + question +"\" and the response was \""+queryRawResponse+"\" Please, just give a concise response in a more friendly way? Please do not give any other suggests or chatter."
            friendlyResponse = getChatGptResponse(friendlyResultsPrompt)
            print("Friendly Response:")
            print(friendlyResponse)
        except Exception as err:
            error = str(err)
            print(err)

        questionResults.append({
            "question": question,
            "sql": sqlSyntaxResponse,
            "queryRawResponse": queryRawResponse,
            "friendlyResponse": friendlyResponse,
            "error": error
        })

    responses["questionResults"] = questionResults

    with open(getPath(f"response_{strategy}_{time()}.json"), "w") as outFile:
        json.dump(responses, outFile, indent = 2)


sqliteCursor.close()
sqliteCon.close()
print("Done!")
