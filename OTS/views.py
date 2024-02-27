from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from OTS.models import Candidate, Question, Result
import random

def welcome(request):
    return render(request, 'welcome.html')

def candidateRegistrationForm(request):
    return render(request, 'registration_form.html')

def candidateRegistration(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        # Check if the user already exists
        if Candidate.objects.filter(username=username).exists():
            userStatus = 1
        else:
            candidate = Candidate()
            candidate.username = username
            candidate.password = request.POST.get('password')
            candidate.name = request.POST.get('name')
            candidate.save()
            userStatus = 2
    else:
        userStatus = 3  # Request method is not POST
    context = {
        'userStatus': userStatus
    }
    return render(request, 'registration.html', context)

def loginView(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        candidate = Candidate.objects.filter(username=username, password=password)
        if len(candidate) == 0:
            loginError = "Invalid username or Password"
            return render(request, 'login.html', {'loginError': loginError})
        else:
            # Login Success
            request.session['username'] = candidate[0].username
            request.session['name'] = candidate[0].name
            return HttpResponseRedirect("home")
    else:
        return render(request, 'login.html')

def candidateHome(request):
    if 'name' not in request.session.keys():
        return HttpResponseRedirect("login")
    else:
        return render(request, 'home.html')

def testPaper(request):
    if 'name' not in request.session.keys():
        return HttpResponseRedirect("login")
    
    # Fetch questions from the database table
    n = int(request.GET.get('n', 1))  # Default to 1 if 'n' is not provided
    question_pool = list(Question.objects.all())  # Changed this line
    random.shuffle(question_pool)
    questions_list = question_pool[:n]
    
    context = {'questions': questions_list}
    return render(request, 'test_paper.html', context)

def calculateTestResult(request):
    if 'name' not in request.session.keys():
        return HttpResponseRedirect("login")
    
    total_attempt = 0
    total_right = 0
    total_wrong = 0
    qid_list = []

    for k in request.POST:
        if k.startswith('qno'):
            qid_list.append(int(request.POST[k]))

    for n in qid_list:
        question = Question.objects.get(qid=n)
        try:
            if question.ans == request.POST['q' + str(n)]:
                total_right += 1
            else:
                total_wrong += 1
            total_attempt += 1
        except:
            pass

    points = (total_right - total_wrong) / len(qid_list) * 10

    # Create a new Result object with relevant data
    result = Result(
        username=Candidate.objects.get(username=request.session['username']),
        attempt=total_attempt,
        right=total_right,
        wrong=total_wrong,
        points=points
    )

    # Save the new Result object to the database
    result.save()

    # Update candidate table
    candidate = Candidate.objects.get(username=request.session['username'])
    candidate.test_attempted += 1
    candidate.points = (candidate.points * (candidate.test_attempted - 1) + points) / candidate.test_attempted
    candidate.save()

    return HttpResponseRedirect('result')

def testResultHistory(request):
    if 'name' not in request.session.keys():
        return HttpResponseRedirect("login")
    
    candidate = Candidate.objects.filter(username=request.session['username'])
    results = Result.objects.filter(username_id=candidate[0].username)
    context = {'candidate': candidate[0], 'results': results}
    return render(request, 'candidate_history.html', context)

def showTestResult(request):
    if 'name' not in request.session.keys():
        return HttpResponseRedirect("login")
    
    # Fetch latest result from result table
    result = Result.objects.filter(resultid=Result.objects.latest('resultid').resultid, username_id=request.session['username'])
    context = {'result': result}
    return render(request, 'show_result.html', context)

def logoutView(request):
    if 'name' in request.session.keys():
        del request.session['username']
        del request.session['name']
    return HttpResponseRedirect("login")
