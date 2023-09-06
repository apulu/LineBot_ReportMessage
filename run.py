from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import sys
import os

app = Flask(__name__)

# Channel Access Token
ChannelAccessToken = 'hJW0O8WBeZcrTq9Rl23Dks5b25APA2vKCiqrGHksEBKlvrxmUULN2uaLM1eW1Wutk+AWum0sIweEWOUm3jQF5497EMlLVgZnDrGCDqM0hJ4d9Lti1CEyhf4Idm3MKHK1n1Npuz6JteynCcZEjR1mmAdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi(ChannelAccessToken)
# Channel Secret
ChannelSecret = '50a41f676728d857765ac69ca22940bd'
handler = WebhookHandler(ChannelSecret)

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# Added manual format -Garrett, 2021.05.10
def msg_manual_report(user_msg, groupID, userName):
    user_msg = user_msg.replace('自訂回報','').strip()
    ID = str(userName)
    reportData[groupID][ID] = user_msg
    tmp_str = str(ID)+'，回報成功。'  
    return tmp_str      

def msg_report(user_msg, groupID):
    try:
        if ( # 檢查資料是否有填，字數注意有換行符
            len(user_msg.split('姓名')[-1].split('學號')[0])<3 and
            len(user_msg.split("學號")[-1].split('手機')[0])<3 and 
            len(user_msg.split('手機')[-1].split('體溫')[0])<3 and 
            len(user_msg.split('體溫')[-1].split('狀況')[0])<3
            ):
            raise Exception
        # 得到學號
        ID = user_msg.split("學號")[-1].split('手機')[0][1:]
        # 直接完整save學號 -Garrett, 2021.01.28  
        ID = str(int(ID)) #先數值再字串，避免換行困擾
        # 學號不再限定只有5碼 -Garrett, 2021.01.28  
        #if len(ID)==6:
        #    ID = int(ID[-4:])
        #elif len(ID)<=4:
        #    ID = int(ID)
    except Exception:
        tmp_str = '請檢查 姓名、學號是否有漏填。'       
    else:
        #reportData[groupID][ID] = user_msg
        reportData[groupID][ID] = user_msg
        tmp_str = str(ID)+'號回報成功\n如需更動，再回報一次即可。'  
    return tmp_str        
        

def msg_readme():
    tmp_str = (
        '小助手指令如下:\n' 
        '----------\n'   
        '•格式\n'
        '  輸出範例格式\n'
        '•已報\n'
        '  列出已回報人員學號\n'
        '•輸出\n'
        '  貼出所有已回報紀錄\n'
        '•清空\n'
        '  手動清空所有回報紀錄\n'
        '----------\n' 
    )
    return tmp_str

def msg_cnt(groupID):
    tmp_str = ''
    try:
        tmp_str = (
            '已完成回報學號如下:\n'
            +str([number for number in sorted(reportData[groupID].keys())]).strip('[]')
        )
    except BaseException as err:
        tmp_str = 'catch error exception: '+str(err)
    return tmp_str

def msg_output(groupID):
    try:
          tmp_str = '報告班長!\n\n'
          for data in [reportData[groupID][number] for number in sorted(reportData[groupID].keys())]:
              tmp_str = tmp_str + data +'\n\n'      
          tmp_str = tmp_str + '謝謝班長!'
    except BaseException as err:
        tmp_str = 'catch error exception: '+str(err)
    #else:
        #reportData[groupID].clear()
    return tmp_str
def msg_format():
    tmp_str = '姓名：\n學號：\n手機：\n體溫：\n狀況：'
    return tmp_str
    
def msg_clear(groupID):
    reportData[groupID].clear()
    tmp_str = '資料已清空'
    return tmp_str
    
def msg_model(groupID):
    tmp_str = '你們到底想怎樣直接說吧'
    return tmp_str

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 各群組的資訊互相獨立
    try:
        groupID = event.source.group_id
    except: # 此機器人設計給群組回報，單兵不可直接一對一回報給機器人
        message = TextSendMessage(text='請直接把我拉進班群再回報')
        line_bot_api.reply_message(event.reply_token, message)
    else:
        userID = event.source.user_id

        g_profile = line_bot_api.get_group_summary(groupID)
        groupName = g_profile.group_name

        u_profile = line_bot_api.get_group_member_profile(groupID,userID)
        userName = u_profile.display_name
        userName = str(userName)

        if not reportData.get(groupID): # 如果此群組為新加入，會創立一個新的儲存區
            reportData[groupID]={}
        LineMessage = ''
        receivedmsg = event.message.text

        if '姓名' in receivedmsg and '學號' in receivedmsg and '手機' in receivedmsg:
            LineMessage = msg_report(receivedmsg,groupID)
        elif '使用說明' in receivedmsg and len(receivedmsg)==4:
            LineMessage = msg_readme()        
        elif '已報' in receivedmsg and len(receivedmsg)==2:
            LineMessage = msg_cnt(groupID)
        elif '格式' in receivedmsg and len(receivedmsg)==2:
            LineMessage = msg_format()
        elif '輸出' in receivedmsg and len(receivedmsg)==2:
            LineMessage = msg_output(groupID)
        # for Error Debug, Empty all data -Garrett, 2021.01.27        
        elif '清空' in receivedmsg and len(receivedmsg)==2:
            LineMessage = msg_clear(groupID)
        #elif '瑋勛' in receivedmsg:
        #    LineMessage = msg_model(groupID)
            
        if LineMessage :
            message = TextSendMessage(text=LineMessage)
            line_bot_api.reply_message(event.reply_token, message)

if __name__ == "__main__":
    global reportData
    reportData = {}
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
