from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from . import forms
from . import models
from superuser.models import Manage_Match
from django.contrib.auth import authenticate, login , update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from challenges.models import ChallengesSolvedBy
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm

def redirect(request) :
	"""
	转跳至登录url
	"""
	return HttpResponseRedirect("login/")

def register(request) :
	template_name = "register/register.html"
	context = {}
	if request.user.is_authenticated : #用户登录过
		return HttpResponseRedirect("/accounts/profile")
	if request.method == 'POST' :
		form = forms.RegisterForm(request.POST)
		if form.is_valid() :
			teamname = form.cleaned_data.get("teamname")
			username = form.cleaned_data.get("username")
			email = form.cleaned_data.get("email")
			password = form.cleaned_data.get("password")
			try :
				user = models.TeamUser.objects.get(username=username) #与数据库中的对比 lyd100
				error = {'form':form, 'error':'用户名已经存在！'}
				return render(request, template_name, error)

			except :
				try:
					#加入队伍
					try:
						max_number = (Manage_Match.objects.first()).team_max_number
					except:
						max_number = 3
					team = models.Teams.objects.get(teamname=teamname) 
					if team.number >= max_number:
						#队伍人满时
						error = {'form':form, 'error':'该队伍人数已满！'}
						return render(request, template_name, error)
					else:
						team.number += 1
						team.save()
						user = models.TeamUser.objects.create_user(username=username, password=password, email=email, team = team)
						user.save()
				except:
					#创建队伍
					new_team = models.Teams()
					new_team.teamname = teamname
					new_team.email = email
					new_team.number += 1
					new_team.save()
					user = models.TeamUser.objects.create_user(username=username, password=password, email=email, team = new_team, is_leader=True)
					user.save()
				login(request, user)
				return HttpResponseRedirect('/challenges/')
	else :
		form = forms.RegisterForm()
	context['form'] = form
	return render(request, template_name, context)

@login_required(login_url="/accounts/login/")
def profile(request) :
	"""
	个人信息
	"""
	template_name = "profile/profile.html"
	context = {}

	if request.user.is_superuser :
		return HttpResponseRedirect("/teams/")
	username = request.user.username
	teamname = models.TeamUser.objects.get(username=username).team.teamname
	job = models.TeamUser.objects.get(username=username).job
	company = models.TeamUser.objects.get(username=username).company
	if request.method == 'POST' :
		form = forms.UpdateTeamUserDetails(request.POST)
		success = 0
		if form.is_valid() :
			job = form.cleaned_data.get("job")
			company = form.cleaned_data.get("company")
			models.TeamUser.objects.filter(username=username).update(job=job, company=company)
			success = 1
			context = {'form':form, 'success':success, 'teamname':teamname}
			return render(request, template_name, context)
	else :
		form_data = {'job':job, 'company':company}
		form = forms.UpdateTeamUserDetails(initial=form_data)
	context['form'] = form
	context['teamname'] = teamname
	return render(request, template_name, context)

@login_required(login_url="/accounts/login/")
def team_view(request) :
	template_name = 'team/team.html'
	context = {} #字典类型，从Views往模板里传递的信息
	if request.user.is_superuser :
		return HttpResponseRedirect("/teams/")

	user_details = models.TeamUser.objects.get(username=request.user.username)
	#select * from TeamUser where username = "lyd"; request.user.username;
	solved_challenges = ChallengesSolvedBy.objects.filter(user_name=request.user)
	#select * from TeamUser where username = "lyd";
	context['user_details'] = user_details
	context['solved_challenges'] = solved_challenges
	return render(request, template_name,context) #（请求，模板的名字，往模板传递的信息他是一个字典类型）

@login_required(login_url="/accounts/login/")
def update_password(request) :
	template_name = 'profile/change-password.html'
	context = {}
	if request.method == 'POST' :
		form = PasswordChangeForm(request.user, request.POST)
		if form.is_valid() :
			user = form.save()
			update_session_auth_hash(request, user)
			messages.success(request, '修改密码成功')
			return HttpResponseRedirect("/challenges/")
		else :
			messages.error(request, '修改密码失败，请检查.')
	else :
		form = PasswordChangeForm(request.user)
	context['form'] = form
	return render(request, template_name, context)

@login_required(login_url="/accounts/login/")
def every_team(request, pk) :
	"""
	"""
	template_name = 'team/team.html'
	context = {}
	requested_team = pk
	try :
		requested_team_details = models.Teams.objects.get(teamname=requested_team)
		# request_teamusers_details = models.TeamUser.objects.filter(team=requested_team_details)
		solved_team_challenges = ChallengesSolvedBy.objects.filter(teamname=requested_team)
		context['user_details'] = requested_team_details
		context['solved_challenges'] = solved_team_challenges
		return render(request, template_name, context)
	except :
		return HttpResponseRedirect("/accounts/team/")
