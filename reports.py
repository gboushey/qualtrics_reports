import pandas as pd

from pandasql import sqldf
pysqldf = lambda q: sqldf(q, globals())

from fpdf import FPDF, HTMLMixin
class HTML2PDF(FPDF, HTMLMixin):
    pass


df = pd.read_csv('data/data.csv')
df_data = df.loc[3:, 'Q2':]

facilitator_col = 'Q25'
group_col = 'Q23'
comment_col = "Q27"
learners_text = "Second-Year Students from Medicine, Nursing, Pharmacy, Dentistry, and Physical Therapy"

def case_stmt(field):
    return "CASE WHEN " + field + " == 'Excellent' THEN 5 \
        WHEN " + field + " == 'Very Good' THEN 4 \
        WHEN " + field + " == 'Good' THEN 3 \
        WHEN " + field + " == 'Fair' THEN 2 \
        WHEN " + field + " == 'Poor' THEN 1 END"

df_report = pysqldf("SELECT " + facilitator_col + " AS FACILITATOR, " + group_col + " AS GRP, "
                    + case_stmt('Q10_1') + " as Q1, " \
                    + case_stmt('Q10_2') + " as Q2, " \
                    + case_stmt('Q10_3') + " as Q3, " \
                    + case_stmt('Q5_1') + " as Q5, " \
                    + comment_col + " AS COMM " \
                    "FROM df_data ORDER BY FACILITATOR, GRP")

unique_fac_grp = pysqldf("SELECT DISTINCT FACILITATOR, GRP FROM df_report WHERE FACILITATOR != 'None' \
                         AND GRP != 'None' ORDER BY FACILITATOR, GRP")

print(unique_fac_grp)

report_data = []

for i in range(len(unique_fac_grp)):
    report_line = []
    sql_str = "SELECT * FROM df_report WHERE FACILITATOR = '" + str(unique_fac_grp.iloc[i][0]) + "' \
AND GRP = '" + str(unique_fac_grp.iloc[i][1]) + "'"
    df_fac_grp = pysqldf(sql_str)

    report_line.append(str(unique_fac_grp.iloc[i][0]).strip())
    report_line.append(str(unique_fac_grp.iloc[i][1]).strip())
    d_group = df_fac_grp.describe()    
    
    q1 = "None"
    q2 = "None"
    q3 = "None"
    q5 = "None"
    
    c1 = 0
    c2 = 0
    c3 = 0
    c5 = 0
    
    if 'Q1' in d_group.keys():
        c1 = int(d_group['Q1'][0])
        q1 = round(d_group['Q1'][1],2)
    if 'Q2' in d_group.keys():
        c2 = int(d_group['Q2'][0])
        q2 = round(d_group['Q2'][1],2)
    if 'Q3' in d_group.keys():
        c3 = int(d_group['Q3'][0])
        q3 = round(d_group['Q1'][1],2)
    if 'Q5' in d_group.keys():
        c5 = int(d_group['Q5'][0])
        q5 = round(d_group['Q5'][1],2)
            
    report_line.append((c1, c2, c3, c5))    
    report_line.append((q1, q2, q3, q5))
    
    comment_string = """SELECT DISTINCT COMM FROM df_report WHERE 
    FACILITATOR = '""" + str(unique_fac_grp.iloc[i][0]) + """' AND 
    GRP = '""" + str(unique_fac_grp.iloc[i][1]) + """'"""
    
    rs_comments = pysqldf(comment_string)
        
    comments = []
    for i in range(len(rs_comments)):
        if rs_comments['COMM'][i] != None:
            comments.append(rs_comments['COMM'][i])
        
    report_line.append(comments)
    report_data.append(report_line)
        
i = 0

for i in range(len(unique_fac_grp)):

    course_info = "<html>"
    course_info += "<b>Facilitator Name:</b> " + str(report_data[i][0]) + "<p/>"
    course_info += "<hr/>"
    
    course_info += "<b><font face=Verdana>IPE Session #3 on Monday, April 22, 2019</font></b><p/>"
    course_info += "<b>Topic:<b/> How will our work get done?<p/>"
    course_info += "<b>Learners:<b/> " + learners_text + "<p/>"
    
    course_info += "<b>Group Name:</b> " + str(report_data[i][1]) + "<p/>"

    ratings = "<p/>"
    ratings += "1= Poor, 2= Fair, 3= Fair, 4= Very Good, 5= Excellent"
    ratings += """<table border="1" align="left" width="100%">
    <thead>
    <tr>
    <th width="56%">How would you rate your small group facilitator's:</th>
    <th width="10%">Count</th>
    <th width="17%">Your Score</th>
    <th width="15%">Average Score</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td>Level Of Preparation</td>
    <td>""" + str(report_data[i][2][0]) + """</td>
    <td>""" + str(report_data[i][3][0]) + """</td>
    <td>""" + str(report_data[i][3][3]) + """</td>
    </tr>
    <tr>
    <td>Ability to facilitate?</td>
    <td>""" + str(report_data[i][2][1]) + """</td>
    <td>""" + str(report_data[i][3][1]) + """</td>
    <td>""" + str(report_data[i][3][3]) + """</td>
    </tr>
    <tr>
    <td>Overall Effectiveness?</td>
    <td>""" + str(report_data[i][2][1]) + """</td>
    <td>""" + str(report_data[i][3][1]) + """</td>
    <td>""" + str(report_data[i][3][3]) + """</td>
    </tr>
    </tbody>
    </table>"""

    comments = "<b>Please include any specific comments about strengths/ suggestions for improvement for your small group facilitator.</b><p/>"
    
    for j in range(len(report_data[i][4])):
        if report_data[i][4][j].strip() != "None" and report_data[i][4][j].strip() != "Na":
            comments += str(report_data[i][4][j].encode("utf-8"))[2:-1] + "<br/>"
    
    comments += "</html>"
    
    pdf = HTML2PDF()
    pdf.add_page()
    pdf.write_html(course_info)
    pdf.write_html(ratings)
    pdf.write_html(comments)
    pdf.output('reports/' + str(report_data[i][0]).replace(" ", "_") + "-" + str(report_data[i][1]).replace(" ", "__")  + '.pdf')