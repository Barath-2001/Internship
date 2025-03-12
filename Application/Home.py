import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import seaborn as sns
import plotly.express as px
from streamlit_option_menu import option_menu
import openpyxl
import datetime
import time
from sklearn.preprocessing import OneHotEncoder
from prophet import Prophet

st.set_page_config(page_title = 'Application')
st.title("Supplier Analysis")
st.markdown("""
<style>
.stButton > button {
    display: block;
    margin: 28px 0px 0px 0px;
}
</style>
""", unsafe_allow_html=True)
with st.sidebar:
    selected=option_menu(
        menu_title='Main Menu',
        options=["Home"]
    )
    file= st.file_uploader(label = 'Upload your dataset:',type=['xlsx','csv'])

if 'flag' not in st.session_state:
    st.session_state.flag = False  
    
# @st.fragment
# def first_dropdown():
#     item_list=list(rej_df['ITEM_ID'].unique())
#     selected_category = st.selectbox('Item',item_list)
#     return selected_category

# @st.fragment
# def second_dropdown(inp3,item_list):
#     diction={}
#     for i in item_list:
#         diction[i]=list(rej_df.loc[rej_df['ITEM_ID']==i]['VENDOR_ID'].unique())
#     selected_subcategory = st.multiselect("Vendor",diction[inp3],diction[inp3][0])
#     return selected_subcategory



# @st.fragment
# def first_dropdown():
#     item_list=list(rej_df['ITEM_ID'].unique())
#     return st.selectbox('Item', item_list, key='dropdown1')

# @st.fragment
# def second_dropdown():
#     if 'dropdown1' in st.session_state:
#         diction={}
#         for i in item_list:
#             diction[i]=list(rej_df.loc[rej_df['ITEM_ID']==i]['VENDOR_ID'].unique())
#         dropdown1 = st.session_state.
#         return st.selectbox('Select Service Level', grouped_dropdowns[dropdown1], key='dropdown2')
@st.cache_resource
def Prophet_model(df,inp3,inp4):
    DF=df.loc[df['TRANSACTION_TYPE']!='RECEIVE'].sort_values(by=['PO_LINE_ID','TRANSACTION_DATE']).copy()
    DF.reset_index(inplace=True)
    DF.drop(columns=['index'],inplace=True)
    DF['ds']=DF['TRANSACTION_DATE'].copy()
    DF['y']=DF['REJECTION_RATE'].copy()
    DF.drop(columns=['PO_LINE_ID','ACTUAL_QUANTITY','TRANSACTION_TYPE','TRANSACTION_DATE','REJECTION_RATE','PROMISED_DATE'],inplace=True)
    # st.write(DF)
    encoder=OneHotEncoder(sparse_output=False)
    encoded = encoder.fit_transform(DF[['VENDOR_ID', 'ITEM_ID']])
    columns = [f"{col}_{int(val)}" for col, vals in zip(['VENDOR', 'ITEM'], encoder.categories_) for val in vals]
    DF[columns] = encoded
    DF.drop(columns=['VENDOR_ID', 'ITEM_ID'], inplace=True)
    model=Prophet()
    for col in columns:
         model.add_regressor(col)
    model.fit(DF)
    future = model.make_future_dataframe(periods=2, freq='M')
    selected_vendor = "VENDOR_"+str(inp3)
    selected_item = "ITEM_"+str(inp4)
    for col in columns:
        future[col] = 1 if col in [selected_vendor, selected_item] else 0
    forecast=model.predict(future)
    # st.write(forecast[['ds','yhat','yhat_lower','yhat_upper']].tail(15))

    time_df=df.loc[df['TRANSACTION_TYPE']=='RECEIVE'].copy()
    time_df['TRANSACTION_DATE']=pd.to_datetime(time_df['TRANSACTION_DATE']).dt.normalize().copy()
    time_df['DAYS']=(time_df['PROMISED_DATE']-time_df['TRANSACTION_DATE']).dt.days.copy()
    # st.write(time_df)
    missed=time_df.loc[time_df['DAYS']<0]['DAYS'].count()
    total=time_df['DAYS'].count()
    percentage=((total-missed)/total)*100
    percentage=round(percentage,1)
    forecast['Forecast Date']=forecast['ds'].copy()
    forecast['Forecaste Rejection Rate']=forecast['yhat'].copy()
    forecast.drop(columns=['ds','yhat'],inplace=True )
    # st.write(total,missed,percentage)
    return forecast,percentage

def Rejection_rate(inp3,inp4):
    if inp3:
        df=df_main.loc[(df_main['VENDOR_ID']==inp3)&(df_main['ITEM_ID']==inp4)].sort_values(by=['TRANSACTION_DATE','PO_LINE_ID']).copy()
    else:
        df=df_main.loc[(df_main['ITEM_ID']==inp4)].sort_values(by=['TRANSACTION_DATE','PO_LINE_ID']).copy()
    qn=dict(df.loc[df['TRANSACTION_TYPE']=='RECEIVE'].groupby(['VENDOR_ID','ITEM_ID','PO_LINE_ID'])['ACTUAL_QUANTITY'].sum())
    rej_rate=[]
    tot_qn={}
    for i,j in qn.items():
        act=df.loc[(df['VENDOR_ID']==i[0])&(df['ITEM_ID']==i[1])&(df['PO_LINE_ID']==i[2])&(df['TRANSACTION_TYPE']=='ACCEPT')].sort_values(by=['TRANSACTION_DATE'])['ACTUAL_QUANTITY'].sum()
        rec=df.loc[(df['VENDOR_ID']==i[0])&(df['ITEM_ID']==i[1])&(df['PO_LINE_ID']==i[2])&(df['TRANSACTION_TYPE']=='RECEIVE')].sort_values(by=['TRANSACTION_DATE'])['ACTUAL_QUANTITY'].sum()
        if act==0:
            tot_qn[i]=rec
        else:
            tot_qn[i]=act

    for index, row in df.iterrows():
        if row['TRANSACTION_TYPE']!='RECEIVE':
            if row['TRANSACTION_TYPE']=='ACCEPT':
                tol=tot_qn[(row['VENDOR_ID'],row['ITEM_ID'],row['PO_LINE_ID'])]
                total=df.loc[(df['VENDOR_ID']==row['VENDOR_ID'])&(df['ITEM_ID']==row['ITEM_ID'])&(df['PO_LINE_ID']==row['PO_LINE_ID'])&(df['TRANSACTION_TYPE']=='ACCEPT')]['ACTUAL_QUANTITY'].sum()
                if total==tol:
                    act=tol-total
                else:
                    print("true")
                    act=tol-row['ACTUAL_QUANTITY']
                rej_rate.append((act/tol)*100)
            else:
                tol=tot_qn[(row['VENDOR_ID'],row['ITEM_ID'],row['PO_LINE_ID'])]
                rej_rate.append((row['ACTUAL_QUANTITY']/tol)*100)
     
    df.insert(5,'REJECTION_RATE',0.0)
    df.loc[df['TRANSACTION_TYPE']!='RECEIVE','REJECTION_RATE']=rej_rate
    return df

@st.cache_resource
def read_data(file):
    po_receiving_data=pd.read_excel(file,na_values='Missing',usecols="D,G,J,N,P:Q,S",engine='openpyxl')
            # st.success("Items with no ID are omitted") 
    # po_receiving_data=read_data(file)
    # st.toast('File upload successfully.', icon="✅")
    st.session_state.flag = True
    df_main=po_receiving_data.copy()   
    st.title("Data")
    df_main['ITEM_ID'].fillna(-1,inplace=True)
    df_main=df_main.loc[(df_main['ITEM_ID']!=-1)].copy()
    st.write(df_main.sample(7).reset_index(drop=True))
    if df_main['ITEM_ID'].dtype != 'O':
        df_main['ITEM_ID']=pd.to_numeric(df_main['ITEM_ID'], downcast='integer', errors='coerce') 
        # st.write(df_main.dtypes)
    df_main['TRANSACTION_DATE']=pd.to_datetime(df_main['TRANSACTION_DATE'])
    # acpt_df=df_main.loc[(df_main['TRANSACTION_TYPE']=='ACCEPT') & (df_main['ITEM_ID']!=-1)].copy()
    # a=pd.to_datetime(acpt_df['TRANSACTION_DATE'])                                                                               
    # acpt_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                                
    # acpt_df.reset_index(drop=True,inplace=True)  
    # acpt_df['MONTH']=acpt_df['TRANSACTION_DATE']
    # acpt_df.set_index('MONTH',inplace=True)     
    # rej_df = df_main.loc[(df_main['ITEM_ID']!=-1) & ((df_main['TRANSACTION_TYPE']=='REJECT'))].copy()
    # rej_df=rej_df.sort_values(by=['TRANSACTION_DATE']).copy()
    # rej_df.reset_index(drop=True, inplace=True)
    # rej_df['MONTH']=rej_df['TRANSACTION_DATE']                                                                                  
    # rej_df.set_index('MONTH',inplace=True)   
    # rej_qn=dict(rej_df.groupby([ 'VENDOR_ID' , 'ITEM_ID' ])['ACTUAL_QUANTITY'].sum())
    # tol_qn={}
    # for i,j in rej_qn.items():
    #     tol_qn[i]=df_main.loc[(df_main['VENDOR_ID']==i[0]) & (df_main['ITEM_ID']==i[1]) & (df_main['TRANSACTION_TYPE']=='RECEIVE')]['ACTUAL_QUANTITY'].sum()
    # rej_rate=[]
    # for index, row in rej_df.iterrows():
    #     tol=tol_qn[(row['VENDOR_ID'],row['ITEM_ID'])]
    #     rej_rate.append((row['ACTUAL_QUANTITY']/tol)*100)
    # rej_df.insert(5,'REJECTION_RATE',rej_rate)
    return df_main
# @st.cache_resource
# def Rejection_Rate(df_main,rej_df):
#     rej_qn=dict(rej_df.groupby([ 'VENDOR_ID' , 'ITEM_ID' ])['ACTUAL_QUANTITY'].sum())
#     tol_qn={}
#     for i,j in rej_qn.items():
#         tol_qn[i]=df_main.loc[(df_main['VENDOR_ID']==i[0]) & (df_main['ITEM_ID']==i[1]) & (df_main['TRANSACTION_TYPE']=='RECEIVE')]['ACTUAL_QUANTITY'].sum()
#     rej_rate=[]
#     for index, row in rej_df.iterrows():
#         tol=tol_qn[(row['VENDOR_ID'],row['ITEM_ID'])]
#         rej_rate.append((row['ACTUAL_QUANTITY']/tol)*100)
#         # del(rej_df['REJECTION_RATE'])
#     return rej_rate
    
if selected=='Home':  
    if file is not None:
        df_main=read_data(file)
        if st.session_state.flag:
            st.toast('File upload successfully.', icon="✅")
            st.session_state.flag=False
        # df_main=po_receiving_data.copy()   
        # st.title("Data")
        # st.write(df_main.sample(7).reset_index(drop=True))
        # df_main['ITEM_ID'].fillna(-1,inplace=True)
        # if df_main['ITEM_ID'].dtype != 'O':
        #     df_main['ITEM_ID']=pd.to_numeric(df_main['ITEM_ID'], downcast='integer', errors='coerce') 
        # # st.write(df_main.dtypes)
        # df_main['TRANSACTION_DATE']=pd.to_datetime(df_main['TRANSACTION_DATE']).dt.normalize().copy()
        # acpt_df=df_main.loc[(df_main['TRANSACTION_TYPE']=='ACCEPT') & (df_main['ITEM_ID']!=-1)].copy()
        # a=pd.to_datetime(acpt_df['TRANSACTION_DATE'])                                                                               
        # acpt_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                                
        # acpt_df.reset_index(drop=True,inplace=True)  
        # # st.header("Accepted data")
        # # st.write(acpt_df.sample(5).reset_index(drop=True)) 
        # acpt_df['MONTH']=acpt_df['TRANSACTION_DATE']
        # acpt_df.set_index('MONTH',inplace=True)     
        # rej_df = df_main.loc[(df_main['ITEM_ID']!=-1) & ((df_main['TRANSACTION_TYPE']=='REJECT'))].copy()
        # rej_df=rej_df.sort_values(by=['TRANSACTION_DATE']).copy()
        # rej_df.reset_index(drop=True, inplace=True)
        # # st.header("Rejection data")
        # # st.write(rej_df.sample(5).reset_index(drop=True))
        # # rej_df['REJECTION_RATE']=0.0                                            
        # # rej_df.reset_index(drop=True, inplace=True)                                                                                 
        # # rej_df['TRANSACTION_TYPE']='REJECT'                                              
        # # a=pd.to_datetime(rej_df['TRANSACTION_DATE'],errors='coerce')                                                                                
        # # rej_df['TRANSACTION_DATE']=pd.to_datetime(a.dt.strftime("%m-%d-%y")).copy()                                         
        # # rej_df.reset_index(drop=True,inplace=True)       
        # rej_df['MONTH']=rej_df['TRANSACTION_DATE']                                                                                  
        # rej_df.set_index('MONTH',inplace=True)   
        # st.header("Analysis")  
        typ=list(df_main['TRANSACTION_TYPE'].unique())
        qnt=[]
        for i in typ:
            qnt.append(df_main.loc[(df_main['TRANSACTION_TYPE']==i)& (df_main['ITEM_ID']!=-1)]['ACTUAL_QUANTITY'].sum())
        # fig,ax=plt.subplots(figsize=(18,6))
        # plt.bar(typ,qnt)
        # for i ,v in enumerate(qnt):
        #     plt.text(i,v,str(v),ha='center')
        # plt.xlabel("Transaction Type")
        # plt.ylabel("Quantity")
        # st.pyplot(fig)
        # key=['ACCEPTED','REJECTED']
        # values=[]
        # values.append(acpt_df['ACTUAL_QUANTITY'].sum())
        # values.append(rej_df['ACTUAL_QUANTITY'].sum())    
        # fig1, ax1 = plt.subplots(figsize=(10,5))
        # ax1.pie(values,labels=key,autopct="%1.1f%%")
        # ax1.axis('equal')  
        # plt.legend()
        # st.pyplot(fig1)
        # rej=dict(rej_df.groupby(["VENDOR_ID"])["ACTUAL_QUANTITY"].sum())
        # rej_vendor=dict(sorted(rej.items(), key=lambda item: item[1],reverse=True))
        # key=list(rej_vendor.keys())
        # value=list(rej_vendor.values())
        # key=[str(i) for i in key]
        # fig = plt.figure(figsize = (10, 5))
        # plt.bar(key[0:5],value[0:5])
        # plt.xlabel("Vendor ")
        # plt.ylabel("Quantity ")
        # plt.title("Top 5 Vendor with highest rejection")
        # for i ,v in enumerate(value[0:5]):
        #     plt.text(i,v,str(v),ha='center')
        # st.pyplot(fig)
        # rej_rate=Rejection_Rate(df_main,rej_df)
        # rej_df.insert(5,'REJECTION_RATE',rej_rate)
        # supp1=list(rej_df['VENDOR_ID'].unique())
        # inp1=st.selectbox(label="Vendor:", options=supp1)
        # diction={}
        # for i in supp1:
        #     diction[i]=list(rej_df.loc[rej_df['VENDOR_ID']==i]['ITEM_ID'].unique())
        # #inp2=st.selectbox(label="Item", options=diction[inp1])

        # inp2 = st.multiselect("Item",diction[inp1],diction[inp1][0])
        # # st.write(inp2)
        # # st.write(rej_df.loc[(rej_df['VENDOR_ID']==inp1)&(rej_df['ITEM_ID'].isin(inp2))])
        # search=st.checkbox("Advance Search") 
        # df1= rej_df.loc[(rej_df['VENDOR_ID']==inp1)&(rej_df['ITEM_ID'].isin(inp2))].sort_values(by=['ITEM_ID','TRANSACTION_DATE','REJECTION_RATE'])
        # start_1=list(df1.sort_values(by=['TRANSACTION_DATE']).head(1)['TRANSACTION_DATE'])
        # end_1=list(df1.sort_values(by=['TRANSACTION_DATE']).tail(1)['TRANSACTION_DATE']) 
        # if search:
        #     date_1=pd.to_datetime(st.date_input("Start date",start_1[0]))
        #     date_2=pd.to_datetime(st.date_input("End date",end_1[0]))
        #     df1= rej_df.loc[(rej_df['VENDOR_ID']==inp1) & (rej_df['ITEM_ID'].isin(inp2)) &(rej_df['TRANSACTION_DATE']>=date_1) &(rej_df['TRANSACTION_DATE']<=date_2) ].sort_values(by=['ITEM_ID','TRANSACTION_DATE','REJECTION_RATE'])
        
        # fig ,ax=plt.subplots()
        # fig = plt.figure(figsize=(12, 4))
        # rej_df.loc[rej_df['VENDOR_ID']==inp1].sort_values(by=['TRANSACTION_DATE']).groupby(['ITEM_ID'])['REJECTION_RATE'].plot(figsize=(12,6),legend=True)
        # fig = px.line(df1, x='TRANSACTION_DATE', y='REJECTION_RATE', color='ITEM_ID', symbol='ITEM_ID', markers=True).update_layout(
        #     xaxis_title="Date", yaxis_title="Rejection Rate")
        # st.plotly_chart(fig,use_container_width=True)
        
        # def Trend(supp,slopes,time,inp):
        #     down_flag=0
        #     month=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        #     up_flag=0
        #     neutral_flag=0
        #     mon=[]
        #     for i in range(len(slopes)):
        #         for j in range(len(slopes[i])):
        #             if slopes[i][j]<0.0:
        #                 up_flag=1
        #             if slopes[i][j]>0.0:
        #                 down_flag=1
        #             if slopes[i][j]==0:
        #                 neutral_flag=1
        #             if slopes[i][j]<0:
        #                 mon.append(time[i])
        #     ne_flag=0
        #     if neutral_flag==1 and up_flag ==0 and down_flag==0:
        #         st.write("Vendor {0} has no irregularity detected".format(inp))
        #         ne_flag=1
        #     elif up_flag==0:
        #         st.write("Vendor {0} have a upward trend  ".format(inp))
        #     elif down_flag==0:
        #         st.write("Vendor {0} have an downward trend".format(inp))
        #     if ne_flag==0:    
        #         cycle_len=3
        #         flag=0
        #         count=0
        #         l=[]
        #         for i in range(len(slopes)):
        #             for j in range(len(slopes[i])):
        #                 if slopes[i][j]>=0:
        #                     count+=1
        #                     if count>=cycle_len:
        #                         if flag!=1:
        #                             l.append(time[j])
        #                             l.append(time[j-1])
        #                             flag=1       
        #                         else :
        #                             l.append(time[j])
        #                             flag=1
        #                 else:
        #                     flag=0
        #                     count=0
        #         if (len(l)!=0):
        #             st.write("The deviation for {0} are in the months of:".format(inp))
        #             l=list(set(l))
        #             for i in l:
        #                 st.write(month[i-1])
       
        # def Slope(df,inp):
        #     supp=list(df['VENDOR_ID'].unique())
        #     slopes=[]
        #     time=list(df['TRANSACTION_DATE'].dt.month)
        #     for i in supp:
        #         y=list(df.loc[df['VENDOR_ID']==i]['REJECTION_RATE'])
        #         slope=[0.0]
        #         N=len(y)
        #         x=[i for i in range(1,N+1)]
        #         for i in range(N):
        #             if i+1<N:
        #                 slope.append((y[i+1]-y[i])/(x[i+1]-x[i]))
        #         slopes.append(slope)
        #     Trend(supp,slopes,time,inp)
        # #     print(y)
        #     return slopes
        
        # Slope(df1,inp1)
        st.title("Input")
        Item_list=list(df_main['ITEM_ID'].unique())
        vendor_list=list(df_main['VENDOR_ID'].unique())
        # st.write(item_list)
        cols=st.columns([2,2,1])
        with cols[0]:
            inp3 = st.selectbox("Vendor",vendor_list,index=None)
        with cols[1]:
            if inp3:
                diction={}
                for i in vendor_list:
                    diction[i]=list(df_main.loc[df_main['VENDOR_ID']==i]['ITEM_ID'].unique())
                inp4= st.selectbox("Item",diction[inp3])
            else:
                inp4= st.selectbox("Item",Item_list)
        with cols[2]:
            submit_button=st.button("Submit")
        
        # lists=list(rej_df.loc[rej_df['ITEM_ID']==inp3]["VENDOR_ID"].unique())
        # inp4=st.selectbox(label="Vendor",options=lists)
        if submit_button:
            st.title("Output")
            temp_df=Rejection_rate(inp3,inp4)
            st.dataframe(temp_df)
            Rejection=temp_df.loc[temp_df['TRANSACTION_TYPE']!='RECEIVE']['REJECTION_RATE'].tail(5).sum()/temp_df.loc[temp_df['TRANSACTION_TYPE']!='RECEIVE']['REJECTION_RATE'].count()
            Rejection=round(Rejection,2)
            if temp_df.loc[temp_df['TRANSACTION_TYPE']!='RECEIVE']['VENDOR_ID'].count()<2:
                st.warning("Select Vedor and Item with more than one data")
            else:
                forecast,percentage=Prophet_model(temp_df,inp3,inp4)
                data={
                    'VENDOR': inp3,
                    'ITEM': inp4,
                    'REJECTION RATE':Rejection,
                    'ON TIME DELIVERY':percentage
                }
                temp_df=pd.DataFrame([data])
                temp_df["ON TIME DELIVERY"] = temp_df["ON TIME DELIVERY"].apply(
                    lambda x: f"🟢 {x}%" if float(x) >= 95.0 else 
                             (f"🟡 {x}%" if float(x) >= 80.0 and float(x) < 95.0 else f"🔴 {x}%")
                )
                temp_df["REJECTION RATE"] = temp_df["REJECTION RATE"].apply(
                    lambda x: f"🟢 {x}%" if float(x) <= 5.0 else 
                             (f"🟡 {x}%" if float(x) > 5.0 and float(x) < 10.0 else f"🔴 {x}%")
                )
                st.dataframe(temp_df)
                forecast["Forecaste Rejection Rate"] = forecast["Forecaste Rejection Rate"].apply(
                    lambda x: f"{round(abs(x), 2)}%"
                )
                # st.write(forecast)

                st.dataframe(forecast[['Forecast Date','Forecaste Rejection Rate']].tail(3))
                
            # temp_df= df_main.loc[(df_main['VENDOR_ID']==inp3)&(df_main['ITEM_ID'].isin(inp4))].sort_values(by=['VENDOR_ID','TRANSACTION_DATE','REJECTION_RATE'])
        # temp_df=rej_df.loc[(rej_df['ITEM_ID']==inp3 )& (rej_df['VENDOR_ID']==inp4)].sort_values(by=['TRANSACTION_DATE','REJECTION_RATE'])
        # search_2=st.checkbox("Advance search")
            # start_2=list(temp_df.head(1)['TRANSACTION_DATE'])
            # end_2=list(temp_df.tail(1)['TRANSACTION_DATE'])   
            
        # if search_2:
        #     date_3=pd.to_datetime(st.date_input("Start Date",start_2[0]))
        #     date_4=pd.to_datetime(st.date_input("End Date",end_2[0]))
        #     temp_df= rej_df.loc[((rej_df['VENDOR_ID']==inp4) & (rej_df['ITEM_ID']==inp3))&(rej_df['TRANSACTION_DATE']>=date_3) &(rej_df['TRANSACTION_DATE']<=date_4) ].sort_values(by=['TRANSACTION_DATE','REJECTION_RATE'])
            
            # fig = px.line(temp_df.loc[temp_df['TRANSACTION_TYPE']!='RECEIVE'], x='TRANSACTION_DATE', y='REJECTION_RATE', color='ITEM_ID', symbol='VENDOR_ID', markers=True).update_layout(
            #     xaxis_title="Date", yaxis_title="Rejection Rate")
            # st.plotly_chart(fig,use_container_width=True)
            # Slope(temp_df,inp4)
        # df2=rej_df.loc[(rej_df['ITEM_ID']==21635887)].sort_values(by=['TRANSACTION_DATE'])
        # fig = px.line(df2, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
        #     xaxis_title="Date", yaxis_title="Rejection Rate")
        # st.plotly_chart(fig,use_container_width=True)
        # start=pd.to_datetime(str(st.date_input("Enter start date", datetime.date(2023, 6, 1))))
        # end = pd.to_datetime(str(st.date_input("Enter end date", datetime.date(2023, 8, 1))))
        # st.write("The dates are :",end-start)
        # df=rej_df.loc[(rej_df['ITEM_ID']==21635887) & (rej_df['TRANSACTION_DATE']>=start) & (rej_df['TRANSACTION_DATE']<=end)].sort_values(by=['TRANSACTION_DATE'])
        # st.write(df.head())
        # fig = px.line(df, x='TRANSACTION_DATE', y='REJECTION_RATE', color='VENDOR_ID', symbol='VENDOR_ID', markers=True).update_layout(
        # xaxis_title="Date", yaxis_title="Rejection Rate")
        # st.plotly_chart(fig,use_container_width=True)
    else:
        st.warning('Upload a File.') 
        
