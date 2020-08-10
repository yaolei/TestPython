from django.shortcuts import render
# from django.shortcuts import render_to_response
from django.http import HttpResponse, JsonResponse
from .DbConnectionAction import *
import os
import time
import json
# print(os.getcwd(), "##########")
# Create your views here.
def userLogin(request):
    if request.method == "POST":
        postBody = request.body
        json_result = json.loads(postBody)
        print(json_result, "######")
        # HttpResponse return to web page
        # JsonResponse return to front end
        return JsonResponse(json_result)
    else:
        return HttpResponse("not post request")

def modify_article(request, art_id):
    return HttpResponse(art_id)

def get_matchDatas(request):
        if request.method == "POST":
            postBody = request.body
            json_result = json.loads(postBody)
            print(json_result, "######")

            result = DbConnection.getMatchDatas(json_result['request_Id'])

            print(result, "@@@@@@@@@@")
            # HttpResponse return to web page
            # JsonResponse return to front end
            return JsonResponse(result, safe=False)
        else:
            return HttpResponse("not post request")
    # reqId = "E013807-16"
    # result = DbConnection.getMatchDatas(reqId)
    # if (result == 1):
    #     sendLodingState("Analyzing !")
    #     resultList = {
    #         "state": result
    #     }
    #     return resultList
    # else:
    #     print(result)
    #     return result
# def sendErrorMessageToFrontEnd(errorState, name):
#     errorMess = ""
#     if (errorState == 9):
#         errorMess = name + " is not valid !"
#     print(errorState, errorMess)
#     return {"state": errorState, "errorMessage": errorMess}

def sendLodingState(waitState):
    titleMessage = "---Data state ：" + waitState
    connectMessage = "Loading wait for " + waitState
    print(titleMessage)
    print(connectMessage, end="")
    for i in range(10):
        print(".", end="", flush=True)
        time.sleep(1)
