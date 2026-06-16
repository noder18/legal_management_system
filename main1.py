import sqlite3

import flet as ft
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os,webbrowser,random
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")
from flet.matplotlib_chart import MatplotlibChart
#import shutil
import sqlite3
import time

 


def init_db():
    conn = sqlite3.connect("legal_datab.db", check_same_thread=False)
    cursor = conn.cursor()
    
    #CASE LIST- storage of all case details
    cursor.execute('''CREATE TABLE IF NOT EXISTS Case_List 
                   (SNo INTEGER, Case_Number VARCHAR(50) UNIQUE,Case_ID VARCHAR(50),Client_ID VARCHAR(50),Petitioner TEXT ,Respondent TEXT,Court_Name TEXT fon, Status TEXT ,Next_Date DATE, Notes TEXT)
                   ''')
    #BILL GENERATION-creates all bills and connects to client
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Bills_Table 
                   (Invoice_No VARCHAR(50) PRIMARY KEY,Client_ID VARCHAR(50),Case_Number VARCHAR(50) UNIQUE,Expenses REAL,Fees REAL,Tax_Amt REAL,Total_Amt REAL, Payment_Status TEXT ,Payment_Date DATE , Mode_of_Payment TEXT)
                   ''')
    cursor.execute('''DROP TABLE Expenses_List_old''')
    cursor.execute('''DROP TABLE User_List''')
    #CLIENT TABLE- client name+ basic contact info
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Client_List
                   (Client_ID TEXT PRIMARY KEY,Client_Name TEXT,Phone_No TEXT,EMAIL TEXT)''')
  
    #EXPENSES TABLE
    cursor.execute('''CREATE TABLE IF NOT EXISTS Expenses_List
                   (Exp_Num INTEGER PRIMARY KEY AUTOINCREMENT,Client_ID VARCHAR(50),Case_Number VARCHAR(50),Amount REAL ,Reason TEXT,Date DATE )
                  ''')
    conn.commit()
    return conn
db_conn=init_db()


def main(page: ft.Page):
    #default theme mode
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.theme = ft.Theme( #lightmode
        color_scheme_seed=ft.Colors.BROWN_100,
        data_table_theme=ft.DataTableTheme(
            heading_row_color=ft.Colors.BROWN_100, decoration=ft.BoxDecoration(
            border=ft.border.all(1.5, ft.Colors.BROWN_300),  
            border_radius=ft.border_radius.all(12),         
        ))
        )

    page.dark_theme = ft.Theme(  #darkmode
        color_scheme_seed=ft.Colors.ORANGE_100,
        data_table_theme=ft.DataTableTheme(
            heading_row_color=ft.Colors.BROWN, decoration=ft.BoxDecoration(
            border=ft.border.all(1.5, ft.Colors.ORANGE_300),  
            border_radius=ft.border_radius.all(12),        
        )))


    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        page.update()

    
    import ollama
    username="admin"
    password="ex#483"
    user_name=ft.TextField(label="Username",prefix_icon=ft.Icons.PERSON,width=300)
    pass_word=ft.TextField(label="Password",prefix_icon=ft.Icons.LOCK,password=True,can_reveal_password=True,width=300)
    notify=ft.Text("",color="red")
    
    def login(e):
        theme_button = ft.ElevatedButton("Toggle Theme", on_click=toggle_theme)
        page.add(theme_button,)
        if user_name.value==username and pass_word.value==password:
            login_page.visible=False
            page.add(main_display)
            display_clientlist()
            display_caselist()
            display_billslist()
            display_expenseslist()
            update_bill_dropdown()
            update_ecaseno_dropdown()
    
            page.update()
            page.open(ft.SnackBar(ft.Text("Welcome!")))
        else:
            notify.value="Invalid username or password. Try again"
            page.update()

    login_page=ft.Container(content=ft.Column([
        ft.Icon(ft.Icons.GAVEL,size=50),
        ft.Text("Login",size=25,weight="bold"),
        user_name,
        pass_word,
        notify,
        ft.ElevatedButton("Enter",on_click=login,width=300),
    ],horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    alignment=ft.alignment.center,
    expand=True,
    visible=True)     

    #####   DASHBOARD CONTENT #####
   

    def get_monthly_data(start_val, end_val):
        if not start_val or not end_val:
            fig, ax = plt.subplots(figsize=(8, 4))
            fig.patch.set_alpha(0.0)
            ax.patch.set_alpha(0.0)
            ax.text(0.5, 0.5, "Select Date Range to View Chart", 
                    ha='center', va='center', color='grey')
            return MatplotlibChart(fig, expand=True)

        start_point=time.time()
        cur = db_conn.cursor()

        cur.execute('''SELECT strftime('%Y-%m', Payment_Date) as period, SUM(Fees) 
                    FROM Bills_Table 
                    WHERE Payment_Date BETWEEN ? AND ?
                    GROUP BY period''', (start_val, end_val))
        rev_dict = dict(cur.fetchall())

        cur.execute('''SELECT strftime('%Y-%m', Date) as period, SUM(Amount) 
                    FROM Expenses_List 
                    WHERE Date BETWEEN ? AND ?
                    GROUP BY period''', (start_val, end_val))
        exp_dict = dict(cur.fetchall())

        from datetime import datetime
        
        start_dt = datetime.strptime(start_val, '%Y-%m-%d')
        end_dt = datetime.strptime(end_val, '%Y-%m-%d')
        
        periods = []
        curr = start_dt.replace(day=1)
        while curr <= end_dt:
            periods.append(curr.strftime('%Y-%m'))
            if curr.month == 12:
                curr = curr.replace(year=curr.year + 1, month=1)
            else:
                curr = curr.replace(month=curr.month + 1)

        rev_values = [rev_dict.get(p, 0) for p in periods]
        exp_values = [exp_dict.get(p, 0) for p in periods]
        labels = [datetime.strptime(p, '%Y-%m').strftime('%b-%y') for p in periods]

        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        x = range(len(periods))
        ax.bar([i - 0.2 for i in x], rev_values, width=0.4, label='Fees', color='#2196F3')
        ax.bar([i + 0.2 for i in x], exp_values, width=0.4, label='Expenses', color='#F44336')

        txt_color = "white" if page.theme_mode == ft.ThemeMode.DARK else "black"
        ax.set_xticks(x)
        ax.set_xticklabels(labels, color=txt_color, rotation=45)
        ax.tick_params(colors=txt_color)
        ax.legend()
        fig.tight_layout()
        return MatplotlibChart(fig, expand=True)
    
    def get_upcoming_hearings():
        cur=db_conn.cursor()
        cur.execute("SELECT Case_Number,Next_Date FROM Case_List WHERE Next_Date>=date('now','localtime') ORDER BY Next_Date ASC LIMIT 3")
        hearings =cur.fetchall()
        if not hearings:
            return ft.Text("No upcoming hearings scheduled.", size=13)
        controls = []
        for case_no, h_date in hearings:
            controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CALENDAR_MONTH),
                title=ft.Text(f"Case: {case_no}", size=14, weight="bold"),
                subtitle=ft.Text(f"Hearing: {h_date}", size=12),
                dense=True,
            )
        )
        return ft.Column(controls, spacing=0)
    
    def display_clientlist():
        cur=db_conn.cursor()
        cur.execute("SELECT Client_ID,Client_Name, Phone_No, EMAIL FROM Client_List")
        rows=cur.fetchall()
        client_table.rows.clear()
        for r in rows:
              client_table.rows.append(            
                    ft.DataRow(cells=[
                                ft.DataCell(ft.Text(r[0])),#cliid
                                ft.DataCell(ft.Row([
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            on_click=lambda e,
                                            row=r: edit_cli(row)),    
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE,
                                            icon_color="red700",
                                            on_click=lambda e,clid=r[0]: deletes_cli(clid)),
                                            ])
                                        ),
                                ft.DataCell(ft.Text(r[1])),#name
                                ft.DataCell(ft.Text(r[2])),#phone no
                                ft.DataCell(ft.Text(r[3])),#email      
                            ])
                        )
        page.update()

    def add_cli(e):
        cid = clientid.value.strip()
        name = client_name.value.strip()
        phone = client_phone.value.strip()
        email = client_email.value.strip()
        
        if not cid:
            clientid.error_text="Client ID is required!"
            clientid.update()
            return
        if not name:
            client_name.error_text="Client Name is required!"
            client_name.update()
            return
        clientid.error_text = None
        client_name.error_text = None

        try:
            cur = db_conn.cursor()
            cur.execute("INSERT INTO Client_List (Client_ID, Client_Name, Phone_No, EMAIL) VALUES (?, ?, ?, ?)",
                        (cid, name, phone, email))
            db_conn.commit()
            clientid.value="";client_name.value="";client_phone.value="";client_email.value=""
            display_clientlist()
            page.update()
            page.open(ft.SnackBar(ft.Text(f"Client {name} added successfully!"), bgcolor="green"))
        except sqlite3.IntegrityError:
            clientid.error_text="Client ID already exists"
            clientid.update()
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red"))
        display_clientlist() 
        page.update()

    def deletes_cli(clid):
        def confirm_delete(e):
            try:
                cur=db_conn.cursor()
                cur.execute("DELETE FROM Client_List WHERE Client_ID = ?",(clid,))
                db_conn.commit()
                page.close(dlg) # Close the popup
                display_clientlist() # Refresh the expense table
                page.snack_bar=ft.SnackBar(ft.Text(f"Client No.{clid} deleted"),bgcolor="red")
                page.snack_bar.open=True
                page.update()
            except Exception as ex:
                print(f"Delete Error: {ex}")
        dlg=ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Client record"),
            content=ft.Text(f"Permanently delete client no.{clid}?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=lambda _: page.close(dlg))])
        page.open(dlg)
        page.update()

    def edit_cli(r):
        page.selected_clid=r[0] 
        clientid.value = str(r[0])
        client_name.value = str(r[1])
        client_phone.value = str(r[2])
        client_email.value = str(r[3])
       
        addcli_btn.visible = False
        updatecli_btn.visible = True
        cancelcli_btn.visible = True
        display_clientlist() 
        page.update()
    
   
    def updates_cli(e):
        cur = db_conn.cursor()
        cur.execute("UPDATE Client_List SET Client_ID=?,Client_Name=?,Phone_No=?,EMAIL=? WHERE Client_ID=?",
                    (clientid.value,client_name.value,client_phone.value,client_email.value,page.selected_clid))
        db_conn.commit()
        clientid.value="";client_name.value="";client_phone.value="";client_email.value=""
        addcli_btn.visible = True
        updatecli_btn.visible = False
        cancelcli_btn.visible = False

        display_clientlist() 
        page.update()
        page.open(ft.SnackBar(ft.Text("Client record updated successfully")))

    def cancel_cli_edit(e):
        clientid.value="";client_name.value="";client_phone.value="";client_email.value=""
        addcli_btn.visible = True
        updatecli_btn.visible = False
        cancelcli_btn.visible = False
        display_clientlist() 
        page.update()

    def save_notes(e):
        page.client_storage.set("saved_case_notes", e.control.value)

    def fetch_complete_case_data(search_case_number):
        cur = db_conn.cursor()
        cur.execute("""SELECT Petitioner, Status, Next_Date FROM Case_List WHERE Case_Number = ?""", (search_case_number,))
        case_data = cur.fetchone()
        if not case_data:
            return None 
        petitioner, status, next_date = case_data
        
        cur.execute("SELECT SUM(Amount) FROM Expenses_List WHERE Case_Number = ?", (search_case_number,))
        expense_row = cur.fetchone()
        total_expenses = expense_row[0] if expense_row[0] is not None else 0
        cur.execute("SELECT Total_Amt FROM Bills_Table WHERE Case_Number = ?", (search_case_number,))
        billing_row = cur.fetchone()
        total_bill = billing_row[0] if billing_row and billing_row[0] is not None else 0

        return {
            "CNR": search_case_number,
            "client_name": petitioner,
            "status": status,
            "next_date": next_date,
            "total_expenses": total_expenses,
            "total_bill": total_bill
        }
    def on_click_view_details(e):
        search_value = cnr_input_field.value.strip()
        
        if not search_value:
            case_overview_panel.content = ft.Container(padding=20,content=ft.Text("Please enter a case number!", color="red", weight=ft.FontWeight.BOLD))
            case_overview_panel.update()
            return
            
        data = fetch_complete_case_data(search_value)
        if not data:
            case_overview_panel.content = ft.Container(padding=20,content=ft.Text("Case number not found in records.", color="red", weight=ft.FontWeight.BOLD))
            case_overview_panel.update()
            return
        status_cleaned = data['status'].lower()
        tag_color = "orange" if "pending" in status_cleaned else "green" if "disposed" in status_cleaned else "blue"

        case_overview_panel.content = ft.Column([
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK, 
                                icon_size=16, 
                                icon_color="#a46d4d",
                                padding=0,
                                on_click=revert_to_quickcase  
                            ),
                            ft.Text(f"Case: {data['CNR']}",size=15),
                            ft.Container(
                                content=ft.Text(data['status'].upper(), size=10),
                                padding=ft.padding.all(5),
                                border_radius=4)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10, thickness=1),
                        ft.Row([
                            ft.Column([
                                ft.Text("Client", size=11),
                                ft.Text(data['client_name'], size=13),], spacing=2),
                            ft.Column([
                                ft.Text("Next Hearing", size=11),
                                ft.Text(str(data['next_date']), size=13),], spacing=2),], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=10, thickness=1),
                        ft.Row([
                            ft.Column([
                                ft.Text("Total Expenses", size=11),
                                ft.Text(f"₹{data['total_expenses']}", weight=ft.FontWeight.BOLD, size=14, color="blue"),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Column([
                                ft.Text("Pending Balance", size=11),
                                ft.Text(f"₹{data['total_bill']}", weight=ft.FontWeight.BOLD, size=14, color="red" if data['total_bill'] > 0 else "green"),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER), ], alignment=ft.MainAxisAlignment.SPACE_AROUND)]
                         ,spacing=10, alignment=ft.MainAxisAlignment.START)
                    
        case_overview_panel.update()
    def revert_to_quickcase(e):
        case_overview_panel.content = initial_search_content
        cnr_input_field.value = "" # Clear the field so it's clean for the next search
        case_overview_panel.update()
  

    saved_text = page.client_storage.get("saved_case_notes") or ""
    
    clientid = ft.TextField(label="Client ID", height=45)
    client_name = ft.TextField(label="Full Name", height=45)
    client_phone = ft.TextField(label="Phone Number", height=45)
    client_email = ft.TextField(label="Email Address", height=45)
    client_table=ft.DataTable(                     
            columns=[
                ft.DataColumn(ft.Text("Client ID")),
                ft.DataColumn(ft.Text("Actions")),
                ft.DataColumn(ft.Text("Client Name")),
                ft.DataColumn(ft.Text("Phone No.")),
                ft.DataColumn(ft.Text("Email Address")),
            ],
            rows=[])
    addcli_btn=ft.ElevatedButton("Add Client",icon=ft.Icons.ADD,on_click=add_cli)
    updatecli_btn=ft.ElevatedButton("Update record",icon=ft.Icons.EDIT,on_click=updates_cli,visible=False)
    cancelcli_btn=ft.ElevatedButton("Cancel Edit",icon=ft.Icons.CANCEL,on_click=cancel_cli_edit,visible=False)
    add_client_card = ft.Container(
        expand=1,
        padding=15,
        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=10,
        content=ft.Column([
            ft.Text("Quick Add Client", weight="bold", size=16),
            clientid,
            client_name,
            client_phone, 
            client_email, 
            addcli_btn,updatecli_btn,cancelcli_btn], spacing=10))
  
    notes_area = ft.TextField(label="Quick Notes",multiline=True,min_lines=5,max_lines=5,hint_text="Type case notes or reminders here...",value=saved_text,on_change=save_notes )
   
    cnr_input_field = ft.TextField(label="Enter CNR Number", prefix_icon=ft.Icons.SEARCH,width=360,height=45,text_size=16)
    start_date=ft.TextField(label="Start Date",read_only=True,
                         suffix_icon=ft.Icons.CALENDAR_MONTH,on_focus=lambda _: open_calendar(start_date),width=300,
                         prefix=ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: setattr(start_date, "value", "")))
    end_date=ft.TextField(label="End Date",read_only=True,
                         suffix_icon=ft.Icons.CALENDAR_MONTH,on_focus=lambda _: open_calendar(end_date),width=300,
                         prefix=ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: setattr(end_date, "value", "")))

    chart_container = ft.Container(content=get_monthly_data("", ""))


    case_overview_panel = ft.Container(
        width=400,
        height=200,
        padding=15,
        border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        content=ft.Column([
            ft.Text("Case Quick Overview", weight=ft.FontWeight.BOLD, size=15,),
            cnr_input_field,
            ft.ElevatedButton("View Case Details", icon=ft.Icons.SEARCH, on_click=on_click_view_details,width=360),
            ft.Text("Enter a case number above and click 'View Case Details'.", size=13)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    initial_search_content = case_overview_panel.content
    dashboard_content = ft.Column([
                    ft.Text("Law Firm Performance Dashboard", size=25, weight="bold"),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([ft.Text("Daily Scratchpad", weight="bold"), notes_area]),
                            expand=1, padding=15, border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=10,),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Upcoming Hearings", weight="bold"),
                                get_upcoming_hearings(),
                                ft.TextButton("View All Schedule", icon=ft.Icons.ARROW_FORWARD)]),
                            expand=1, padding=15, border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), border_radius=10,),
                        case_overview_panel,
                        add_client_card ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("Financial Overview", size=20, weight="bold"),
                        start_date,end_date], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(content=chart_container,height=400,width=1000,alignment=ft.alignment.center,padding=10),
                    ft.Divider(),
                    client_table], visible=True, expand=True, scroll=ft.ScrollMode.AUTO)

    #####    CASE LIST   ##### 
    page.current_date_target = None 
    
    def on_date_selected(e):
        if e.control.value: 
            formatted_date = e.control.value.strftime("%Y-%m-%d")
            page.current_date_target.value = formatted_date
            page.close(datepicker) 
            page.current_date_target = None
            page.update()
        if start_date.value and end_date.value:
            chart_container.content = get_monthly_data(start_date.value, end_date.value)
            page.update()
        datepicker.open = False 
        page.update()
    def on_calendar_dismissal(e):
        page.close(datepicker) 
        page.current_date_target = None
        page.update()

    datepicker = ft.DatePicker(on_change=on_date_selected,on_dismiss=on_calendar_dismissal,first_date=datetime(2024, 1, 1),last_date=datetime(2027, 12, 31),)
    page.overlay.append(datepicker)

    def open_calendar(target_field):
        page.current_date_target = target_field
        page.open(datepicker) 
        page.update()

    def display_caselist(user_search=""):    
        cur=db_conn.cursor()
        if user_search:
            query="""SELECT SNo,Case_Number,Case_ID,Client_ID,Petitioner,Respondent,Court_Name,Status,Next_Date,Notes FROM Case_List
            WHERE Case_Number LIKE ? OR Petitioner LIKE ? OR Respondent LIKE ?"""
            val=f"%{user_search}%"
            cur.execute(query,(val,val,val))
        else:
            cur.execute("SELECT SNo,Case_Number,Case_ID,Client_ID,Petitioner,Respondent,Court_Name,Status,Next_Date,Notes FROM Case_List")
        rows=cur.fetchall()
        case_table.rows.clear()

        sno_counter=1
    
        for r in rows:
            cno=r[1]
            status_str=str(r[7]).strip().lower()
            status_color=None

            if "pending" in status_str:
                status_color="orange"
            elif "disposed" in status_str:
                status_color="green"
            elif "hearing" in status_str:
                status_color="blue"
            today=datetime.now().strftime("%Y-%m-%d")
            is_today=(str(r[8])==today)

            case_table.rows.append(            
                        ft.DataRow(cells=[
                                ft.DataCell(ft.Text(str(sno_counter))),#sno
                                ft.DataCell(ft.Row([
                                            ft.IconButton(
                                                ft.Icons.EDIT_OUTLINED,
                                                on_click=lambda e,
                                                row=r: edit_case(row)), 
                                            ft.IconButton(
                                                ft.Icons.UPLOAD_FILE_OUTLINED,
                                                icon_color="blue",
                                                on_click=lambda e,num=cno: (setattr(file_picker, "data", num),  
                                                file_picker.pick_files(allow_multiple=True))),
                                            ft.IconButton(
                                                ft.Icons.DELETE_OUTLINE,
                                                icon_color="red700",
                                                on_click=lambda e,num=cno: deletes_case(num)),
                                                ])
                                            ),
                                ft.DataCell(ft.Text(r[1])),#caseno
                                ft.DataCell(ft.Text(r[2])),#local id
                                ft.DataCell(ft.Text(f"{r[4]}({r[3]})")),#petitioner(client_id)
                                ft.DataCell(ft.Text(r[5])),#respondent
                                ft.DataCell(ft.Text(r[6])),#court nm
                                ft.DataCell(ft.Text(r[7],color=status_color)),#case status
                                ft.DataCell(ft.Text(str(r[8]),color="red" if is_today else None,
                                weight="bold" if is_today else "normal")),#date
                                ft.DataCell(ft.Text(r[9])),#notes
                            ])
                        )
            sno_counter+=1
        page.update()
    
    def adds_case(e):

        if len(case_no.value or "") != 16: #ensures length of case_no
            case_no.error_text = "Exactly 16 characters required!"
            case_no.update()
            return  
        case_no.error_text=None
        try:
            cur=db_conn.cursor()
            cur.execute("INSERT INTO Case_List (Case_Number,Case_ID,Client_ID,Petitioner,Respondent,Court_Name,Status,Next_Date,Notes) VALUES(?,?,?,?,?,?,?,?,?)",
                        (case_no.value,lccase_id.value,client_id.value,petitioner.value,respondent.value,court_nm.value,cs_status.value,cs_date.value,addn_notes.value))
            db_conn.commit()
            display_caselist()
            update_ecaseno_dropdown() 
            update_bill_dropdown()
            case_no.value=""; lccase_id.value="";client_id.value="";petitioner.value="";respondent.value="";court_nm.value="";cs_status.value=None;cs_date.value="";addn_notes.value=""
            page.update()
        except sqlite3.IntegrityError:
            case_no.error_text="Error: the case number already exists"
            case_no.update()
        except Exception as ex:
            print(f"Error adding case: {ex}")

    def deletes_case(case_no):
        def confirm_box(e):
            cur = db_conn.cursor()
            cur.execute("DELETE FROM Case_List WHERE Case_Number = ?", (case_no,))
            db_conn.commit()
            
            page.close(box) 
            display_caselist()
            page.snack_bar = ft.SnackBar(ft.Text(f"Case {case_no} deleted"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

        box=ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(f"Permanently delete case {case_no}?"),
            actions=[
                ft.TextButton("Yes",on_click=confirm_box),
                ft.TextButton("No",on_click=lambda _: page.close(box)),],)
        page.open(box)
        page.update()

    def edit_case(r):
        page.selected_case= r[1]
        case_no.value = r[1]
        lccase_id.value = r[2]
        client_id.value=r[3]
        petitioner.value = r[4]
        respondent.value = r[5]
        court_nm.value = r[6]
        cs_status.value = r[7]
        cs_date.value = r[8]
        addn_notes.value = r[9]

        add_btn.visible = False
        update_btn.visible = True
        cancel_btn.visible = True
        page.update()

    def upload_files(e):
        c_no = e.control.data
        if e.files and c_no :
            folder_path = f"./case_folder/{c_no}"
            os.makedirs(folder_path, exist_ok=True)

            upload_list = []
            for file in e.files:
                upload_list.append(
                    ft.FilePickerUploadFile(name=file.name,upload_url=page.get_upload_url(f"/{c_no}/{file.name}", 600)))
            file_picker.upload(files=upload_list)

            page.open(ft.SnackBar(ft.Text(f"Saved {len(e.files)} files into Case {c_no} succesfully")))
            page.update()
    file_picker = ft.FilePicker(on_result=upload_files)
    page.overlay.append(file_picker) 
    page.update()

    def updates_case(e):
        cur=db_conn.cursor()
        cur.execute("""UPDATE Case_List SET Case_Number=?, Case_ID=?,Client_ID=?,Petitioner=?, Respondent=?, Court_Name=?, Status=?, Next_Date=?, Notes=?
        WHERE Case_Number=?""",
                    (case_no.value, lccase_id.value, client_id.value,petitioner.value, respondent.value, court_nm.value, cs_status.value, cs_date.value, addn_notes.value, page.selected_case))
        cur.execute("""UPDATE Expenses_List SET Case_Number = ? WHERE Case_Number = ?""", (case_no.value, page.selected_case))
        cur.execute("""UPDATE Bills_Table SET Case_Number = ? WHERE Case_Number = ?""", (case_no.value, page.selected_case))

        db_conn.commit()
        case_no.value="";lccase_id.value="";client_id.value="";petitioner.value="";respondent.value="";court_nm.value="";cs_status.value=None;cs_date.value="";addn_notes.value=""
        add_btn.visible =True
        update_btn.visible =False
        cancel_btn.visible=False

        update_ecaseno_dropdown()    
        update_bill_dropdown()       
        display_caselist()           
        display_billslist()          
        display_expenseslist()       
        page.update()
        page.open(ft.SnackBar(ft.Text("Case updated successfully")))

    def cancelling_edit(e):
        for f in [case_no, lccase_id, client_id,petitioner, respondent, court_nm, cs_status, cs_date, addn_notes]:
            f.value = ""
        add_btn.visible = True
        update_btn.visible = False
        cancel_btn.visible = False
        display_caselist()
        page.update()

    sno=ft.TextField(label="Sno.",width=300)
    case_no=ft.TextField(label="CNR",max_length=16,counter="0/16",width=300)
    lccase_id=ft.TextField(label=" Local Case ID",width=300)
    client_id=ft.TextField(label="Client ID",width=300)
    petitioner=ft.TextField(label="Petitioner Name",width=300)
    respondent=ft.TextField(label="Respondent Name",width=300)
    court_nm=ft.TextField(label="Court Name",width=300)
    cs_status=ft.Dropdown(
        label="Case Status",
        filled="True",width=300,
        options=[
            ft.dropdown.Option("Pending"),
            ft.dropdown.Option("Disposed"),
            ft.dropdown.Option("Adjourned")])
    cs_date=ft.TextField(label="Next Hearing Date",read_only=True,
                         suffix_icon=ft.Icons.CALENDAR_MONTH,on_focus=lambda _: open_calendar(cs_date),width=300,
                         prefix=ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: setattr(cs_date, "value", "")))
    addn_notes=ft.TextField(label="Additional Notes",width=300)

    add_btn=ft.ElevatedButton("Add to List",icon=ft.Icons.ADD,on_click=adds_case)
    update_btn=ft.ElevatedButton("Update List",icon=ft.Icons.EDIT,on_click=updates_case,visible=False)
    cancel_btn=ft.ElevatedButton("Cancel Edit",icon=ft.Icons.CANCEL,on_click=cancelling_edit,visible=False)
    search_box=ft.TextField(label="Search by CNR or Client Name",prefix_icon=ft.Icons.SEARCH,
                                on_change=lambda e: display_caselist(e.control.value))
    case_table=ft.DataTable(                     
        columns=[
            ft.DataColumn(ft.Text("SNo")),
            ft.DataColumn(ft.Text("Actions")),
            ft.DataColumn(ft.Text("Case No")),
            ft.DataColumn(ft.Text("Local Case ID")),
            ft.DataColumn(ft.Text("Petitioner(Client ID)")),
            ft.DataColumn(ft.Text("Respondent")),
            ft.DataColumn(ft.Text("Court Name")),
            ft.DataColumn(ft.Text("Case Status")),
            ft.DataColumn(ft.Text("Next Hearing Date")),
            ft.DataColumn(ft.Text("Additional Notes")),
        ],
        rows=[])
    
    tracker_content=ft.Column([ 
        #total_cases_text,
        ft.Text("Case List",size=25,weight="bold"),
        ft.Row([sno,case_no,lccase_id,client_id]),
        ft.Row([petitioner,respondent,court_nm]),
        ft.Row([cs_status,cs_date,addn_notes]),
        ft.Row([
           add_btn,update_btn,cancel_btn
        ]),
        ft.Divider(),
        ft.Text("Active Case Status",size=20),
        search_box,
        ft.Row(controls=[case_table],scroll=ft.ScrollMode.ALWAYS,)
    ],visible=False,scroll=ft.ScrollMode.AUTO)
        

    #####    BILL CONTENT #####
    def display_billslist(is_tax_registered=False):
        cur=db_conn.cursor()
        cur.execute("SELECT Invoice_No, Case_Number,Client_ID, Expenses, Fees, Tax_Amt,Total_Amt, Payment_Status, Payment_Date, Mode_of_Payment FROM Bills_Table")
        rows = cur.fetchall()
        bill_table.rows.clear()
        for r in rows:
            
            invb_no = r[0]
            fees = r[4] or 0
            expenses = r[3] or 0
            db_tax=float(r[5] or 0)
            db_total=float(r[6] or 0)

            tax_display = "N/A (Unregistered)"
            tax_display=r[5]
            total_amt = fees + expenses
            total_amt=r[6]

            if is_tax_registered:
                gst_calc = fees * 0.18
                total_amt = fees + expenses + gst_calc
                tax_display = f"₹{gst_calc:.2f}"
                total_str=f"₹{total_amt:.2f}"
            else:
                tax_display=f"₹{db_tax:.2f}"
                total_str=f"₹{db_total:.2f}"

            status_str = str(r[7]).strip().lower()
            status_color = "white"
            if "paid" in status_str:
                status_color = "green"
            elif "pending" in status_str:
                status_color = "orange"
            elif "overdue" in status_str:
                status_color = "red"

            # 5. Build the Row
            bill_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"INV{r[0]}")), # Invoice No
                    ft.DataCell(ft.Row([
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            on_click=lambda e,
                                            row=r: editbill_case(row)),    
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE,
                                            icon_color="red700",
                                            on_click=lambda e,num=invb_no: deletebill(num)),
                                        ft.IconButton(
                                            ft.Icons.PICTURE_AS_PDF_OUTLINED,
                                            icon_color="blue700",
                                            on_click=lambda e, row=r: view_billpdf(row)),    
                                            ])),
                    ft.DataCell(ft.Text(f"{r[2]}({r[1]})")), # Client & Case
                    ft.DataCell(ft.Text(f"₹{expenses:.2f}")), # Fees
                    ft.DataCell(ft.Text(f"₹{fees:.2f}")), # Expenses
                    ft.DataCell(ft.Text(tax_display, color="blue" if is_tax_registered else "grey")), # Dynamic Tax
                    ft.DataCell(ft.Text(f"{total_str}", weight="bold")), # Total
                    ft.DataCell(ft.Text(r[7], color=status_color)), # Status
                    ft.DataCell(ft.Text(r[8])),#payt date
                    ft.DataCell(ft.Text(r[9])),#payt mode
                ])
            )
    page.update()

    def update_bill_dropdown():
        cur = db_conn.cursor()
        cur.execute("SELECT Case_Number FROM Case_List")
        cases = cur.fetchall()
        # Create the list of options
        b_caseno.options = [ft.dropdown.Option(str(c[0])) for c in cases]
        b_caseno.update()
        if b_caseno.page:
            b_caseno.page.update()
    def autoadd_expclient(selected_case_no):
        if not selected_case_no:
            return
        cur = db_conn.cursor()
        cur.execute("SELECT Client_ID FROM Case_List WHERE Case_Number = ?", (selected_case_no,))
        result = cur.fetchone()
        b_cli_id.value = str(result[0]) if result else "Not Found"
        page.update()

    def add_bill(e):
        if not b_caseno.value:
            b_caseno.error_text = "Please select a case!"
            b_caseno.update()
            return
        if not invb_no.value:
            invb_no.error_text = "Invoice number required!"
            invb_no.update()
            return
        invb_no.error_text=None
        b_caseno.error_text=None
        try:
            cur = db_conn.cursor()
            selected_case = str(b_caseno.value).strip()
            cur.execute("SELECT SUM(Amount) FROM Expenses_List WHERE Case_Number = ?", (b_caseno.value,))
            res_exp = cur.fetchone()

            current_expenses = float(res_exp[0]) if res_exp and res_exp[0] is not None else 0.0
            real_fees = float(b_fees.value) if b_fees.value else 0.0
            tax_amt = real_fees * 0.18 if tax_switch.value else 0.0
            total_amt = current_expenses+ real_fees + tax_amt

            cur.execute("SELECT 1 FROM Bills_Table WHERE Case_Number = ?", (b_caseno.value,))
            if cur.fetchone():
                b_caseno.error_text = "Error: This case already has an assigned bill"
                b_caseno.update()
                return

            cur.execute("INSERT INTO Bills_Table (Invoice_No, Client_ID,Case_Number, Expenses, Fees, Tax_Amt,Total_Amt, Payment_Status, Payment_Date, Mode_of_Payment) VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (invb_no.value,b_cli_id.value,b_caseno.value,current_expenses,real_fees,tax_amt,total_amt,pay_s.value,pay_dt.value,pay_md.value) )
            db_conn.commit()
            display_billslist(is_tax_registered=tax_switch.value) 
            invb_no.value="";b_caseno.value =None;b_cli_id.value ="";b_exp.value ="";b_fees.value = "";b_txamt.value = "";b_tamt.value="";pay_s.value=None;pay_dt.value="";pay_md.value=None
            b_caseno.error_text = None
            page.update()
            page.open(ft.SnackBar(ft.Text("Bill added successfully!")))
        except sqlite3.IntegrityError as err:
            if "Invoice_No" in str(err):
                invb_no.error_text = "Error: the bill number already exists"
                invb_no.update()
            else:
                b_caseno.error_text = "Database Integrity Error"
                b_caseno.update()
        except Exception as ex:
            print(f"Error adding bill: {ex}")

    def editbill_case(r):
        page.selected_invno= r[0]
        invb_no.value=r[0]
        b_caseno.value=r[1]
        b_cli_id.value=r[2]
        b_exp.value=r[3]
        b_fees.value=r[4]
        b_txamt.value=r[5]
        b_tamt.value=r[6]
        pay_s.value=r[7]
        pay_dt.value=r[8]
        pay_md.value=r[9]

        addbill_btn.visible = False
        updatebill_btn.visible = True
        cancelbill_btn.visible = True
        page.update()

    def updates_bill(e):
        cur = db_conn.cursor()

        new_fees = float(b_fees.value or 0)
        new_expenses = float(b_exp.value or 0)
        new_tax = new_fees * 0.18 if tax_switch.value else 0.0
        new_total = new_fees + new_expenses + new_tax

        cur.execute('''UPDATE Bills_Table SET Client_ID=?,Case_Number=?,Expenses=?,Fees=?,Tax_Amt=?,Total_Amt=?,Payment_Status=?,Payment_Date=?,Mode_of_Payment=? WHERE Invoice_No=?''',
                    (b_cli_id.value,b_caseno.value,new_expenses,new_fees,new_tax,new_total,pay_s.value,pay_dt.value,pay_md.value,page.selected_invno))
        db_conn.commit()
        cancel_billedit(None) 
        
        addbill_btn.visible = True
        updatebill_btn.visible = False
        cancelbill_btn.visible = False

        display_billslist() 
        page.update()
        page.open(ft.SnackBar(ft.Text("Bill record updated successfully")))
        
    def cancel_billedit(e):
        b_caseno.value =None;b_cli_id.value ="";b_exp.value ="";b_fees.value = "";b_txamt.value = "";b_tamt.value="";pay_s.value=None;pay_dt.value="";pay_md.value=None
        addbill_btn.visible = True
        updatebill_btn.visible = False
        cancelbill_btn.visible = False
        display_billslist() 
        b_caseno.error_text = None
        page.update()
    
    def deletebill(invb_no):
        def confirm_delete(e):
            try:
                cur=db_conn.cursor()
                cur.execute("DELETE FROM Bills_Table WHERE Invoice_No = ?",(invb_no,))
                db_conn.commit()
                page.close(dlg) 
                display_billslist() 
                page.snack_bar=ft.SnackBar(ft.Text(f"Invoice No.{invb_no} deleted"),bgcolor="red")
                page.snack_bar.open=True
                page.update()
            except Exception as ex:
                print(f"Delete Error: {ex}")
        dlg=ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Bill"),
            content=ft.Text(f"Permanently delete invoice no.{invb_no}?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=lambda _: page.close(dlg))])
        page.open(dlg)
        page.update()
    def view_billpdf(row):
        try:
            case_num = row[1]
            fees_val = float(row[4] or 0)
            exp_val = float(row[3] or 0)
            tax_val = float(row[5] or 0)
            
            has_tax = True if tax_val > 0 else False
            pdf_name = generate_pdf(case_num, fees_val, exp_val, has_tax)
            page.open(ft.SnackBar(ft.Text(f"Invoice generated: {pdf_name}"), bgcolor="green"))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor="red"))

    def generate_pdf(case_number,fees,expenses,has_tax):
        cur = db_conn.cursor()
        cur.execute("SELECT Petitioner, Client_ID FROM Case_List WHERE Case_Number = ?", (case_number,))
        cli_value= cur.fetchone()
       
        client_name = cli_value[0] if cli_value else "N/A"
        client_id = cli_value[1] if cli_value else "N/A"

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="LEGAL INVOICE", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", size=11)
        pdf.cell(100, 8, txt=f"Client: {client_name}", ln=0)
        pdf.cell(90, 8, txt=f"Date: {datetime.now().strftime('%d-%m-%Y')}", ln=1, align='R')
        pdf.cell(100, 8, txt=f"Case No: {case_number}", ln=1)
        pdf.ln(5)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(130, 10, "Description", 1, 0, 'L', True)
        pdf.cell(60, 10, "Amount (INR)", 1, 1, 'C', True)

        pdf.set_font("Arial", size=11)
        pdf.cell(130, 10, "Total Fees", 1)
        pdf.cell(60, 10, f"{fees:.2f}", 1, 1, 'R')
        pdf.cell(130, 10, "Total Expenses", 1)
        pdf.cell(60, 10, f"{expenses:.2f}", 1, 1, 'R')

        tax_amount = 0.0
        if has_tax:
            tax_amount = fees * 0.18
            pdf.cell(130, 10, "GST (18%)", 1)
            pdf.cell(60, 10, f"{tax_amount:.2f}", 1, 1, 'R')

        grand_total = fees + expenses + tax_amount
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(130, 12, "GRAND TOTAL", 1, 0, 'L', True)
        pdf.cell(60, 12, f"Rs. {grand_total:.2f}", 1, 1, 'R', True)

        
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 5, txt="Note: This is a system-generated invoice.", ln=True)
        file_name = f"Invoice_{client_name.replace(' ', '_')}.pdf"
        pdf.output(file_name)
        return file_name


    invb_no=ft.TextField(label="Invoice No.",width=300)
    b_cli_id=ft.TextField(label="Client ID",read_only=True,width=300)
    b_caseno=ft.Dropdown(label="Select CNR",
                          on_change=lambda e:autoadd_expclient(e.control.value),
                          options=[],width=300)
    b_exp=ft.TextField(label="Expense Amt",width=300)
    b_fees=ft.TextField(label="Firm Fees.",width=300)
    b_txamt=ft.TextField(label="Tax Amt",width=300)
    b_tamt=ft.TextField(label="Total Amt.",width=300)
    pay_s=ft.Dropdown(label="Payt. Status",width=300,
                      options=[
            ft.dropdown.Option("Paid"),
            ft.dropdown.Option("Pending"),
            ft.dropdown.Option("Overdue")])
    pay_dt=ft.TextField(label="Payt. Date",width=300,
                         read_only=True,
                         suffix_icon=ft.Icons.CALENDAR_MONTH,on_focus=lambda _: open_calendar(pay_dt),
                         prefix=ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: setattr(pay_dt, "value", "")))
    pay_md=ft.Dropdown(label="Mode of Payt.",width=300,
                       options=[
                           ft.dropdown.Option(key="",text="-"),
                           ft.dropdown.Option("Cash"),
                           ft.dropdown.Option("Cheque"),
                           ft.dropdown.Option("NEFT"),
                           ft.dropdown.Option("UPI"),
                       ])
    
    tax_switch = ft.Switch(
    label="Tax Registered (GST)",
    value=False, 
    on_change=lambda e: [display_billslist(is_tax_registered=e.control.value),page.update()])
    addbill_btn=ft.ElevatedButton("Add bill",icon=ft.Icons.ADD,on_click=add_bill)
    updatebill_btn=ft.ElevatedButton("Update Bill",icon=ft.Icons.EDIT,on_click=updates_bill,visible=False)
    cancelbill_btn=ft.ElevatedButton("Cancel Bill",icon=ft.Icons.CANCEL,on_click=cancel_billedit,visible=False)

    bill_table=ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Invoice No.")),
            ft.DataColumn(ft.Text("Actions")),
            ft.DataColumn(ft.Text("Client ID(Case No.)")),
            ft.DataColumn(ft.Text("Expenses")),
            ft.DataColumn(ft.Text("Firm Fees")),
            ft.DataColumn(ft.Text("Tax Amt")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Payt Status")),
            ft.DataColumn(ft.Text("Payt Date")),
            ft.DataColumn(ft.Text("Mode of Payt")),
        ],
        rows=[]
    )
    bill_content=ft.Column([
        ft.Text("Bill Table",size=25,weight="bold"),
        ft.Row([tax_switch]),
        ft.Row([invb_no,b_caseno,b_cli_id]),
        ft.Row([b_exp,b_fees,b_txamt,b_tamt]),
        ft.Row([pay_s,pay_dt,pay_md]),
        ft.Row([addbill_btn,updatebill_btn,cancelbill_btn]),
        ft.Divider(),
        ft.Row(controls=[bill_table],scroll=ft.ScrollMode.ALWAYS,)
        ],visible=False,scroll=ft.ScrollMode.AUTO)
                                        
  
    #####   EXPENSES CONTENT #####
    def display_expenseslist(uexp_search=""):
        
        cur=db_conn.cursor()
        if uexp_search:
            query="""SELECT Exp_Num,Case_Number,Client_ID,Amount,Reason,Date FROM Expenses_List
            WHERE Case_Number LIKE ? OR Client_ID LIKE ?
            ORDER BY Date DESC"""
            val=f"%{uexp_search}%"
            cur.execute(query,(val,val))
            rows=cur.fetchall()
            
        else:
            cur.execute("SELECT Exp_Num,Case_Number,Client_ID,Amount,Reason,Date FROM Expenses_List ORDER BY Date DESC")
            rows=cur.fetchall()
        exp_table.rows.clear()

        for r in rows:
            exp_table.rows.append(            
                    ft.DataRow(cells=[
                            ft.DataCell(ft.Text(f"EXP{r[0]}")),#expno
                            ft.DataCell(ft.Row([
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            on_click=lambda e,
                                            row=r: edit_exp(row)),    
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE,
                                            icon_color="red700",
                                            on_click=lambda e,eid=r[0]: deletes_exp(eid)),
                                            ])
                                        ),
                            ft.DataCell(ft.Text(r[1])),#caseno
                            ft.DataCell(ft.Text(r[2])),#clientid
                            ft.DataCell(ft.Text(r[3])),#amount
                            ft.DataCell(ft.Text(r[4])),#reason
                            ft.DataCell(ft.Text(r[5])),#date
                            
                            ])
                        )
        page.update()    

    def update_ecaseno_dropdown():
        cur = db_conn.cursor()
        cur.execute("SELECT Case_Number, Petitioner FROM Case_List")
        cases = cur.fetchall()
        
        # Clear old options and add fresh ones
        ecase_no.options = [
            ft.dropdown.Option(key=c[0], text=f"{c[0]} ({c[1]})") 
            for c in cases
        ]
        ecase_no.update() 
        if ecase_no.page:
            ecase_no.page.update()

    def autoadd_clientid(selected_case_no):
        if not selected_case_no:
            cli_id.value = ""
            page.update()
            return
        cur = db_conn.cursor()
        cur.execute("SELECT Client_ID FROM Case_List WHERE Case_Number = ?", (selected_case_no,))
        result = cur.fetchone()
        if result:
            cli_id.value = str(result[0]) 
        else:
            cli_id.value = "Not Found"
            
        page.update() # Refresh to show the new value

    def add_exp(e):
        if not ecase_no.value:
            ecase_no.error_text = "Please select a case!"
            ecase_no.update()
            return
        if not e_amt.value:
            e_amt.error_text = "Enter an amount"
            e_amt.update()
            return
        try:
            float(e_amt.value)
        except ValueError:
            e_amt.error_text = "Amount must be a number"
            e_amt.update()
            return
        try:
            cur = db_conn.cursor()
            cur.execute("INSERT INTO Expenses_List (Client_ID, Case_Number, Amount, Reason, Date) VALUES(?,?,?,?,?)",
                    (cli_id.value,ecase_no.value,e_amt.value,e_type.value,e_date.value))
            db_conn.commit()
            display_expenseslist() 
            
            ecase_no.value =None;cli_id.value ="";e_amt.value ="";e_type.value = "";e_date.value = ""
            ecase_no.error_text = None
            e_amt.error_text = None
            page.update()
            page.open(ft.SnackBar(ft.Text("Expense added successfully!")))
        except sqlite3.IntegrityError:
            e_amt.error_text=""
        except Exception as ex:
            print(f"Error adding expense: {ex}")

    def deletes_exp(eno):
        def confirm_delete(e):
            try:
                cur=db_conn.cursor()
                cur.execute("DELETE FROM Expenses_List WHERE Exp_Num = ?",(eno,))
                db_conn.commit()
                page.close(dlg) 
                display_expenseslist() 
                page.snack_bar=ft.SnackBar(ft.Text(f"Expense No.{eno} deleted"),bgcolor="red")
                page.snack_bar.open=True
                page.update()
            except Exception as ex:
                print(f"Delete Error: {ex}")
        dlg=ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Expense"),
            content=ft.Text(f"Permanently delete expense no.{eno}?"),
            actions=[
                ft.TextButton("Yes", on_click=confirm_delete),
                ft.TextButton("No", on_click=lambda _: page.close(dlg))])
        page.open(dlg)
        page.update()

    def edit_exp(r):
        page.selected_eno=r[0] 
        ecase_no.value = str(r[1])
        cli_id.value = str(r[2])
        e_amt.value = str(r[3])
        e_type.value = str(r[4])
        e_date.value = str(r[5])
        addexp_btn.visible = False
        updateexp_btn.visible = True
        cancelexp_btn.visible = True
        page.update()

    def updates_exp(e):
        cur = db_conn.cursor()
        cur.execute("""UPDATE Expenses_List SET Case_Number=?,Client_ID=?,Amount=?,Reason=?,Date=? WHERE Exp_Num=?""",
                    (ecase_no.value,cli_id.value,e_amt.value,e_type.value,e_date.value,page.selected_eno))
        db_conn.commit()
        ecase_no.value = None;cli_id.value ="";e_amt.value ="";e_type.value ="";e_date.value =""

        addexp_btn.visible = True
        updateexp_btn.visible = False
        cancelexp_btn.visible = False

        display_expenseslist() 
        page.update()
        page.open(ft.SnackBar(ft.Text("Expense record updated successfully")))

    def cancelling_edit(e):
        ecase_no.value = None;cli_id.value ="";e_amt.value ="";e_type.value ="";e_date.value =""
        addexp_btn.visible = True
        updateexp_btn.visible = False
        cancelexp_btn.visible = False
        display_expenseslist() 
        ecase_no.error_text = None
        e_amt.error_text = None
        page.update()

    eno=ft.TextField(label="ExpNo.",width=300)
    cli_id=ft.TextField(label="Client ID",read_only=True,width=300)
    ecase_no=ft.Dropdown(label="Select CNR",
                          on_change=lambda e:autoadd_clientid(e.control.value),
                          options=[],
                          width=300)
    e_amt=ft.TextField(label="Amount",width=300)
    e_type=ft.TextField(label="Reason",width=300)
    e_date=ft.TextField(label="Date(YYYY-MM-DD)",read_only=True,suffix_icon=ft.Icons.CALENDAR_MONTH,on_focus=lambda _: open_calendar(e_date),
                        width=300,prefix=ft.IconButton(ft.Icons.CLEAR, on_click=lambda _: setattr(e_date, "value", "")))
   

    addexp_btn=ft.ElevatedButton("Add Expense",icon=ft.Icons.ADD,on_click=add_exp)
    updateexp_btn=ft.ElevatedButton("Update Expenses",icon=ft.Icons.EDIT,on_click=updates_exp,visible=False)
    cancelexp_btn=ft.ElevatedButton("Cancel Edit",icon=ft.Icons.CANCEL,on_click=cancelling_edit,visible=False)
    esearch_box=ft.TextField(label="Search by CNR or Client ID",prefix_icon=ft.Icons.SEARCH,
                                on_change=lambda e: display_expenseslist(e.control.value))#pass search text to cases_rows)

    exp_table=ft.DataTable(                     #listing cols for display
        columns=[
            ft.DataColumn(ft.Text("ExpNo")),
            ft.DataColumn(ft.Text("Actions")),
            ft.DataColumn(ft.Text("Case No")),
            ft.DataColumn(ft.Text("Client ID")),
            ft.DataColumn(ft.Text("Amount")),
            ft.DataColumn(ft.Text("Reason")),
            ft.DataColumn(ft.Text("Date(YYYY-MM-DD)"))
        ],
        rows=[])
    expenses_content=ft.Column([ 
        #total_cases_text,
        ft.Text("Expenses List",size=25,weight="bold"),
        ft.Row([eno,ecase_no,cli_id]),
        ft.Row([e_amt,e_type,e_date]),
        ft.Row([
           addexp_btn,updateexp_btn,cancelexp_btn
        ]),
        ft.Divider(),
        ft.Text("Active Expenses",size=20),
        esearch_box,
        ft.Row(controls=[exp_table],scroll=ft.ScrollMode.ALWAYS,)
    ],visible=False,scroll=ft.ScrollMode.AUTO)

    #####   AI CONTENT  #####
     
    def get_ai_response(e):
        user_query=ai_input.value.strip()
        if not user_query: 
            return
        display_query.value = user_query
        display_query.visible = True
        ai_response.value="*LOADING THE RESPONSE....*"
        page.update()
        chat_history.append({'role': 'user','content': user_query})

        try:
            display_query.visible=True
            response=ollama.chat(
                model='llama3.2:1b',
                messages=chat_history,
                stream=False)
            ai_response.value=response['message']['content']
            chat_history.append({'role':'assistant','content':ai_response.value})
        except Exception as ex:
            ai_response.value=f"⚠️ **Local Error:** {ex}\n*Make sure the Ollama app is running*"
           
        ai_input.value=""
        page.update()

    chat_history=[]
    ai_input=ft.TextField(
        label="Ask the AI",
        multiline=True,
        min_lines=3,
        max_lines=5,
        border_color="blue")
    display_query = ft.TextField(read_only=True, label="Your query", visible=False )
    ai_response=ft.Markdown(
        "Your AI legal insights will appear here.",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,)
    ai_content=ft.Column([
        ft.Text("Legal AI Assistant",size=25,weight="bold"),
        ft.Text("Research laws,summarize cases , or draft legal point.",italic=True),
        ft.Divider(),
        display_query,
        ft.Container(
            content=ai_response,
            padding=20,
            border=ft.border.all(1,ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.05,ft.Colors.ON_SURFACE_VARIANT),
            expand=True
        ),
        ft.Row([
            ai_input,
            ft.FloatingActionButton(icon=ft.Icons.SEND,on_click=get_ai_response)
        ])   
    ],visible=False,expand=True,scroll=ft.ScrollMode.AUTO)


    ##### DISPLAY AREA ######
    def nav_change(e):
    
        dashboard_content.visible=(e.control.selected_index==0)
        tracker_content.visible=(e.control.selected_index==1)
        expenses_content.visible=(e.control.selected_index==2)
        bill_content.visible=(e.control.selected_index==3)
        ai_content.visible=(e.control.selected_index==4)
        page.update()
    rail= ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.INSERT_CHART,label="DASHBOARD"),
            ft.NavigationRailDestination(icon=ft.Icons.GAVEL,label="CASES"),
            ft.NavigationRailDestination(icon=ft.Icons.WALLET_OUTLINED,label="EXPENSES"),
            ft.NavigationRailDestination(icon=ft.Icons.RECEIPT,label="BILLING"),
            ft.NavigationRailDestination(icon=ft.Icons.QUESTION_MARK_SHARP,label="AI ASSISTANT"),
        ],
        on_change=nav_change,
        
    )
    main_display=(ft.Row([
        rail,
        ft.VerticalDivider(width=1),
        ft.Column([
        ft.Container(
            content=ft.Column([
            dashboard_content,    
            tracker_content,
            expenses_content,
            bill_content,
            ai_content
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True),
            expand=True,
            padding=20)],
            expand=True)],expand=True))
    page.add(login_page)
    page.update()

# STEP 3: RUN THE APP
if __name__ == "__main__":
    ft.app(target=main, upload_dir="case_folder",view=ft.AppView.WEB_BROWSER)
#FLET_APP