##
## this script generates pdf reports for facilitator feedback from quatrics
##
## facilitator names can be in one of two columns, Facilitator #1, or Facilitator #2
## for each faciliator, the script calculates the average
##  - level of preparation
##  - ability to facilitate discussion
##  - overall level of preparation
##  - interprofessional collaboration
##
## overview of script
##
## input is a qualtrics csv file holding info on a survey of facilitators
## including the facilitator name and a 1-5 rating for the questions 
##
## because these values can be for either Facilitator #1 or #2, the script runs 
## two queries. The queries are converted into two dataframes and vertically stacked
## (pandas equivalent of a UNION query).
## 
## the script populates a PDF with those generated values and some other text 
## supplied 

import sys
import pandas as pd

from pandasql import sqldf
pysqldf = lambda q: sqldf(q, globals())

from fpdf import FPDF, HTMLMixin
class HTML2PDF(FPDF, HTMLMixin):
    pass

df = pd.read_csv('data/data_1.13.20.csv')
df_data = df.loc[3:, 'Q2':]

facilitator_col = ['Q16', 'Q22']
#no longer using group
#group_col = 'Q4'
comment_col = ['Q20', 'Q26']
level_of_preparation = ['Q18_1', 'Q24_1']
ability_facilitate_discussion = [ 'Q18_2', 'Q24_2']
overall_level_preparation = ['Q18_3', 'Q24_3']
interprofessional_collaboration = 'Q5_1'

learners_text = "First Year Students from Medicine, Nursing, Pharmacy, Dentistry, and Physical Therapy"
topic = "Roles and Responsibilities"
session = "IPE Session #2 on Monday, January 13, 2020"
avg_preparation= 4.70
avg_facilitation = 4.67
avg_effectiveness = 4.68

def case_stmt(field):
    return "CASE WHEN " + field + " == 'Excellent' THEN 5 \
        WHEN " + field + " == 'Very Good' THEN 4 \
        WHEN " + field + " == 'Good' THEN 3 \
        WHEN " + field + " == 'Fair' THEN 2 \
        WHEN " + field + " == 'Poor' THEN 1 END"

def facilitator_query(i):
    fac_query = pysqldf("SELECT " + facilitator_col[i] + " AS FACILITATOR, "
                        + case_stmt(level_of_preparation[i]) + " as Q1, " \
                        + case_stmt(ability_facilitate_discussion[i]) + " as Q2, " \
                        + case_stmt(overall_level_preparation[i]) + " as Q3, " \
                        + case_stmt(interprofessional_collaboration) + " as Q5, " \
                        + comment_col[i] + " AS COMM " \
                        "FROM df_data ORDER BY FACILITATOR")
    
    return fac_query
                    
q0 = facilitator_query(0)
q1 = facilitator_query(1)

facilitator_df = pd.concat([q0, q1], axis=0)

df_averages = pysqldf("SELECT FACILITATOR, COUNT(*), AVG(Q1), AVG(Q2), AVG(Q3), AVG(Q5) FROM facilitator_df GROUP BY FACILITATOR")

#unique_fac_grp = pysqldf("SELECT DISTINCT FACILITATOR, GRP FROM df_report WHERE FACILITATOR != 'None' \
#                         AND GRP != 'None' ORDER BY FACILITATOR, GRP")



# doing some basic checking if field is blank, but if people type 'Na', or "None', it'll show up...
def facilitator_comments(facilitator):
    return pysqldf("SELECT DISTINCT COMM FROM facilitator_df WHERE FACILITATOR = '" 
        + facilitator + "' AND FACILITATOR IS NOT NULL \
        AND FACILITATOR != '' and FACILITATOR != 'None'")
    

for i in range(0,len(df_averages)):

    facilitator_data = df_averages.iloc[i]
    
    if facilitator_data[0] is not None and facilitator_data[0].strip() is not '-':
        
        course_info = "<html>"
        course_info += "<b>Facilitator Name:</b> " + str(facilitator_data[0]) + "<p/>"
        course_info += "<hr/>"
    
        course_info += "<b><font face=Verdana>" + session + "</font></b><p/>"
        course_info += "<b>Topic:<b/> " + topic + "<p/>"
        course_info += "<b>Learners:<b/> " + learners_text + "<p/>"
    
        ratings = "<p/>"
        ratings += "1= Poor, 2= Fair, 3= Fair, 4= Very Good, 5= Excellent"
        ratings += """<table border="1" align="left" width="100%">
        <thead>
        <tr>
        <th width="56%">How would you rate your small group facilitator's:</th>
        <th width="12%">Responses</th>
        <th width="15%">Your Score</th>
        <th width="15%">Average Score</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td>Level Of Preparation</td>
        <td>""" + str(facilitator_data[1]) + """</td>
        <td>""" + str(round(facilitator_data[2], 2)) + """</td>
        <td>""" + str(avg_preparation) + """</td>
        </tr>
        <tr>
        <td>Ability to facilitate?</td>
        <td>""" + str(facilitator_data[1]) + """</td>
        <td>""" + str(round(facilitator_data[3],2)) + """</td>
        <td>""" + str(avg_facilitation) + """</td>
        </tr>
        <tr>
        <td>Overall Effectiveness?</td>
        <td>""" + str(facilitator_data[1]) + """</td>
        <td>""" + str(round(facilitator_data[4],2)) + """</td>
        <td>""" + str(avg_effectiveness) + """</td>
        </tr>
        </tbody>
        </table>"""

        comments = "<b>Please include any specific comments about strengths/ suggestions for improvement for your small group facilitator.</b><p/>"

        comment_list = facilitator_comments(facilitator_data[0])['COMM'].to_list()
    
        for c in comment_list:
            if c is not None:
                comments += str(c.encode("utf-8"))[2:-1] + "<br/>"
    
        comments += "</html>"
    
        pdf = HTML2PDF()
        pdf.add_page()
        pdf.write_html(course_info)
        pdf.write_html(ratings)
        pdf.write_html(comments)
        
        print(facilitator_data[0])
        
        pdf.output('reports_by_facilitator/' + str(facilitator_data[0]).replace(" ", "-") + '.pdf')