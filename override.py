from mitmproxy import http

# Override response content for patternator.js
# This one only contains png files totally transparent
# So no thunder/snow icon in raindrop layer anymore
def response(flow: http.HTTPFlow):    
    if flow.request.path.endswith("ptype2_v4.png"):        
        flow.response.content = open("/app/resources/ptype2_v4.png", "rb").read()
