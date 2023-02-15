import pulp
from datetime import date, timedelta

def optimize_park_scheduling(days, parks, companies):
    """
    Optimizes the park schedule based on given constraints and conditions

    Parameters:
    days (list): List of days
    parks (list): List of dictionaries, where each dictionary represents a park
    companies (list): List of dictionaries, where each dictionary represents a park company
    
    Returns:
    None
    """

    # Create a LP problem
    problem = pulp.LpProblem("Park Schedule Optimization", pulp.LpMinimize)

    # Create a list of park names
    park_names = [x["name"] for x in parks]

    # Create variables that represent park schedule, 
    variables = pulp.LpVariable.dicts("park_schedule", (park_names, days), 0, 1, pulp.LpInteger)

    # Create slack variables for constraints 6, 7 and 8
    slack_variables_6 = pulp.LpVariable.dicts("slack_6", (park_names), 0, 1, pulp.LpInteger)
    slack_variables_7 = pulp.LpVariable.dicts("slack_7", (park_names, park_names, days, days), 0, 1, pulp.LpContinuous)
    slack_variables_8 = pulp.LpVariable.dicts("slack_8", (park_names, park_names, days, days), 0, 1, pulp.LpContinuous)

    # Define penalty values for slack variables
    PENALTY_6 = 10000
    PENALTY_7 = 10000
    PENALTY_8 = 10000

    problem +=  PENALTY_6 * pulp.lpSum([slack_variables_6[p] for p in park_names]) + \
                PENALTY_7 * pulp.lpSum([slack_variables_7[p1][p2][d1][d2] for p1 in park_names for p2 in park_names for d1 in days for d2 in days]) + \
                PENALTY_8 * pulp.lpSum([slack_variables_8[p1][p2][d1][d2] for p1 in park_names for p2 in park_names for d1 in days for d2 in days])

    # Constraint 1: Only one park can be assigned to the same day
    for d in days:
        problem += pulp.lpSum([variables[p][d] for p in park_names]) <= 1, ("Constraint 1: At maximum one park can be assigned on the same day " + str(d))

    # Constraint 2: Each park must be assigned to a day
    for p in park_names:
        problem += pulp.lpSum([variables[p][d] for d in days]) == 1, ("Constraint 2: Park " + str(p) + " must be assigned to a day.")

    # Constraint 3: Parks that cannot be visited on specific days
    for p in parks:
        for d in p["cannot_visit_days"]:
            problem += variables[p["name"]][d] == 0, ("Constraint 3: Park " + str(p["name"]) + " cannot be visited on the specific day " + str(d))   

    # Constraint 4: Parks that must be visited on specific days
    for p in parks:
        if(p["must_visit_day"] != None):
            problem += variables[p["name"]][p["must_visit_day"]] == 1, ("Constraint 4: Park " + str(p["name"]) + " should be visited on day " + str(p["must_visit_day"]))    

    # Constraint 5: Parks that should be avoided on specific days
    for p in parks:
        for d in p["days_to_avoid"]:
            problem += variables[p["name"]][d] == 0, ("Constraint 5: Park " + str(p["name"]) + " should be avoided on day(s) " + str(d))

    # Constraint 6: Preferred days for visiting a specific park
    for p in parks: 
        pulp.lpSum([variables[p["name"]][d] for d in p["preferred_days"]]) + slack_variables_6[p["name"]] == 1, ("Constraint 6: It is preferred to visit park" + str(p["name"]) + " on days " + str(p["preferred_days"]))

    # Constraint 7: Two demanding parks cannot be assigned on consecutive days
    for d1 in days[:-1]:
        for idx, p1 in enumerate(parks[:-1]):
            if(p1["demanding"]):
                for p2 in parks[idx+1:]:
                    if(p2["demanding"]):
                        d2 = d1 + timedelta(days=1) 
                        problem += variables[p1["name"]][d1] + variables[p2["name"]][d2] <= 1 + slack_variables_7[p1["name"]][p2["name"]][d1][d2], ("Constraint 7: demanding parks cannot be assigned on consecutive days. Parks " + str(p1["name"]) + " and " + str(p2["name"] + ". Days: " + str(d1) + " and " + str(d2)))
                        problem += variables[p1["name"]][d2] + variables[p2["name"]][d1] <= 1 + slack_variables_7[p1["name"]][p2["name"]][d1][d2], ("Constraint 7: demanding parks cannot be assigned on consecutive days. Parks " + str(p1["name"]) + " and " + str(p2["name"] + ". Days: " + str(d2) + " and " + str(d1)))
    
    # Constraint 8: Parks of the same company should be visited within a specific time interval
    for c in companies:
        for idx, p1 in enumerate(parks[:-1]):
            if(c["company"] == p1["company"]):
                for p2 in parks[idx+1:]:
                    if(c["company"] == p2["company"]):
                        for idx2, d1 in enumerate(days[:-1]):
                            for d2 in days[idx2+1:]:
                                delta = d2 - d1
                                if(delta.days + 1 > c["number_of_days"]):
                                    problem += variables[p1["name"]][d1] + variables[p2["name"]][d2] <= 1 + slack_variables_8[p1["name"]][p2["name"]][d1][d2], ("Parks of the same company should be visited within a specific time interval. Parks " + str(p1["name"]) + " and " + str(p2["name"] + ". Days: " + str(d1) + " and " + str(d2)))
                                    problem += variables[p1["name"]][d2] + variables[p2["name"]][d1] <= 1 + slack_variables_8[p1["name"]][p2["name"]][d2][d1], ("Parks of the same company should be visited within a specific time interval. Parks " + str(p1["name"]) + " and " + str(p2["name"] + ". Days: " + str(d2) + " and " + str(d1)))
    
    # Solve the problem
    problem.solve(pulp.PULP_CBC_CMD(timeLimit=300))

    # Print the status of the solution
    print("Status:", pulp.LpStatus[problem.status])
    print("Objective function: ", pulp.value(problem.objective))
    # Print the solution if a solution is found
    if(problem.status >= 0):
        for x in days:
            for y in parks:
                value = variables[y["name"]][x].varValue
                if(value):
                    print(str(x) + " - " + str(y["name"]))

# Defining the first and last day of the trip
first_day =date(year=2022, month=9, day=16)
last_day = date(year=2022, month=9, day=28)
days = [first_day + timedelta(days=x) for x in range(0, (last_day-first_day).days + 1)]

# Defining the parks with its respective company, if it is demanding and the day preferences and restricitions 
magic_kingdom = {"name" : "Magic Kingdom", "company": "Disney", "demanding" : True, "cannot_visit_days": [], "must_visit_day": None,                     
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=19),
                    date(year=2022, month=9, day=24), date(year=2022, month=9, day=25), date(year=2022, month=9, day=26)], 
                    "preferred_days": []}

animal_kingdom = {"name" : "Animal Kingdom", "company": "Disney", "demanding" : False, "cannot_visit_days": [], "must_visit_day": None, 
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

epcot = {"name" : "Epcot", "company": "Disney", "demanding" : True, "cannot_visit_days": [], "must_visit_day": None, 
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

hollywood_studios = {"name" : "Hollywood Studios", "company": "Disney", "demanding" : True, "cannot_visit_days": [], "must_visit_day": None, 
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

universal_islands_of_adventure = {"name" : "Universal Islands of Adventure", "company": "Universal", "demanding" : True, "cannot_visit_days": [], "must_visit_day": None, 
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

universal_studios = {"name" : "Universal Studios", "company": "Universal", "demanding" : True, "cannot_visit_days": [], "must_visit_day": None, 
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

aquatica = {"name" : "Aquatica", "company": "Sea World", "demanding" : False, "cannot_visit_days": [], "must_visit_day": None, "days_to_avoid": [], "preferred_days": []}

busch_gardens = {"name" : "Busch gardens", "company": "Sea World", "demanding" : True, "cannot_visit_days": [], "must_visit_day": None,
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

sea_world = {"name" : "Sea World", "company": "Sea World", "demanding" : False, "cannot_visit_days": [], "must_visit_day": None,                     
                "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                "preferred_days": []}

discovery_cove = {"name" : "Discovery Cove", "company": "Sea World", "demanding" : False, "cannot_visit_days": [], "must_visit_day": date(year=2022, month=9, day=20),
                    "days_to_avoid": [date(year=2022, month=9, day=17),date(year=2022, month=9, day=18),date(year=2022, month=9, day=24), date(year=2022, month=9, day=25)], 
                    "preferred_days": []}

parks = [magic_kingdom, animal_kingdom, epcot, hollywood_studios, universal_islands_of_adventure, universal_studios, aquatica, busch_gardens, sea_world, discovery_cove]

# Defining the entertainment park companies and the number of days the ticket bundle expires
disney = {"company": "Disney", "number_of_days": 7}
sea_world = {"company": "Sea World", "number_of_days": 14}
universal = {"company": "Universal", "number_of_days": 5}

companies = [disney, sea_world, universal]

# Call the function to solve the problem
optimize_park_scheduling(days, parks, companies)