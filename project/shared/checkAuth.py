import jwt

from project.keys import super_secret

#jwt = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiQWtzaGF5IEt1bGthcm5pIiwiZW1haWwiOiJha3NoYXlrdWxrYXJuaS4yMTA0QGdtYWlsLmNvbSJ9.GahsHW9zUtcZG-Q1heh-VC3zayNdaV2eDPl3U_yriKA

def checkAuth(request):
    token = request.headers.get('Authorization')
    if token:
        tokens = token.split(" ")
        if len(tokens)==2:
            auth_str,jwt_token = tokens
            if auth_str=='Bearer' and jwt_token:
                payload = jwt.decode(jwt_token,super_secret,algorithm='HS256')
                return 200,payload['id']
            else:
                return 400,False
        else:
                return 400,False
    else:
        return 401,False