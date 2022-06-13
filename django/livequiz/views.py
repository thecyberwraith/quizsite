from django.shortcuts import render

def join(request):
    return render(request, 'livequiz/join.html')

def play(request, game_code: str):
    return render(request, 'livequiz/participate.html', {'game_code': game_code})