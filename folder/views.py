from django.shortcuts import render, redirect
from django.views import generic
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.utils.decorators import method_decorator

from .models import Folder, ProblemPlace
from problems.models import Problem
from tags.models import Tag
from tags.views import tag_types
from users.permissions import has_access_to_folder, url_403, staff_only

import unicodedata, re
def convert_pretty_to_folder_name(pretty):
    pretty = unicodedata.normalize('NFD', pretty)
    pretty = u"".join([c for c in pretty if not unicodedata.combining(c)])
    pretty = pretty.replace('ł', 'l')
    pretty = pretty.replace('Ł', 'L')
    folder = ''
    for c in pretty:
        if c.isalnum():
            folder += c
        else:
            folder += '-'
    return re.sub('-+', '-', folder)

# remove '/' and '/' around folder_path
def fix_path(folder_path):
    if folder_path[0] == '/':
        folder_path = folder_path[1:]
    if folder_path and folder_path[-1] == '/':
        folder_path = folder_path[:-1]
    return folder_path

def get_folder(folder_path):
    folder_path = fix_path(folder_path)
    root_list = Folder.objects.filter(parent=None)
    assert len(root_list) == 1
    root = root_list[0]
    if folder_path == 'all':
        return root

    folder_path = folder_path.split('/')
    folder = root
    for s in folder_path:
        folder = Folder.objects.filter(parent=folder, folder_name=s)
        if len(folder) == 0:
            raise Http404("Nie istnieje taka ścieżka")
        assert len(folder) == 1
        folder = folder[0]
    return folder

def get_parent_path(path):
    if path != 'all' and '/' in path:
        return path[0:path.rindex('/')]
    else:
        return 'all'

def get_son_path(parent, folder_name):
    if parent == 'all':
        return folder_name
    return parent + '/' + folder_name

def get_parent_paths(path):
    ret_list = []
    path = path.split('/')
    prefix = ''
    for s in path:
        if prefix != '':
            prefix += '/'
        prefix += s
        f = get_folder(prefix)
        ret_list.append((prefix, f.pretty_name))
    return ret_list

def get_context(path):
    path = fix_path(path)
    folder = get_folder(path)
    group_type = tag_types.index("Grupa")
    all_tags = Tag.objects.filter(type_id=group_type).order_by('type_id', 'id')
    selected_tags = []
    for tag in all_tags:
        if folder.tag_set.filter(pk=tag.pk).exists():
            selected_tags.append(tag)
    problems = []
    for fp in ProblemPlace.objects.filter(folder=folder).order_by('place').all():
        problems.append(fp.problem)

    return {
        'folder_path': path,
        'folder': folder,
        'sons': Folder.objects.filter(parent=folder).order_by('pretty_name'),
        'son_path_prefix': path + '/' if path != 'all' else '',
        'parent_path': get_parent_path(path),
        'parent_paths': get_parent_paths(path),
        'problems': problems,
        'all_tags': all_tags,
        'selected_tags': selected_tags,
    }

class IndexView(generic.View):
    def get(self, request, folder_path):
        if not has_access_to_folder(request.user, get_folder(folder_path)):
            return redirect(url_403)
        context = get_context(folder_path)
        if not request.user.is_staff:
            context['sons'] = []
            for son in Folder.objects.filter(parent=context['folder']).all():
                if has_access_to_folder(request.user, son):
                    context['sons'].append(son)
        context['problems'] = []
        for fp in ProblemPlace.objects.filter(folder=context['folder']).order_by('place').all():
            problem = fp.problem
            context['problems'].append(
                    (problem, problem.claiming_user_set.filter(id=request.user.id).exists()))
        return render(request, 'folder/index.html', context)

@method_decorator(staff_only, name='dispatch')
class EditView(generic.View):
    def get(self, request, folder_path):
        return render(request, 'folder/edit.html', get_context(folder_path))

@method_decorator(staff_only, name='dispatch')
class AddFolder(generic.View):
    def post(self, request, folder_path):
        folder = get_folder(folder_path)
        pretty_name = request.POST['pretty_name']
        folder_name = convert_pretty_to_folder_name(pretty_name)
        if folder_name == '' or folder_name == '-':
            messages.error(request, 'Nazwa folderu jest pusta.')
            return redirect('folder:edit', folder_path)

        if not Folder.objects.filter(parent=folder, folder_name=folder_name):
            son = Folder(
                parent=folder,
                pretty_name=pretty_name,
                folder_name=folder_name,
                created_by=request.user,
                show_solution=folder.show_solution,
                show_stats=folder.show_stats,
            )
            son.save()
            messages.success(request, 'Dodano folder!')
        else:
            messages.error(request, 'Taki folder już istnieje.')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class EditFolderName(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        pretty_name = request.POST['pretty_name']
        folder_name = convert_pretty_to_folder_name(pretty_name)
        if folder_name == '' or folder_name == '-':
            return redirect('folder:edit', folder_path)
        if folder_path == 'all':
            messages.error(request, 'Nie można zmienić nazwę głównego folderu.')
            return redirect('folder:edit', folder_path)
        parent_f = get_folder(get_parent_path(folder_path))
        if Folder.objects.filter(parent=parent_f, folder_name=folder_name):
            messages.error(request, 'Taki folder już istnieje.')
            return redirect('folder:edit', folder_path)

        f.folder_name = folder_name
        f.pretty_name = pretty_name
        f.save()
        messages.success(request, 'Zmieniono nazwę!')
        new_path = get_son_path(get_parent_path(folder_path), folder_name)
        return redirect('folder:edit', new_path)

@method_decorator(staff_only, name='dispatch')
class DeleteFolder(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        pretty_name = request.POST['pretty_name']
        matches = Folder.objects.filter(parent=f, pretty_name=pretty_name)
        if len(matches) != 1:
            messages.error(request, 'Nastąpił błąd krytyczny.')
            return redirect('folder:edit', folder_path)
        son = matches[0]

        son.delete()
        messages.success(request, 'Usunięto!')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class AddProblem(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        p_id = request.POST['p_id']
        if p_id == '':
            return redirect('folder:edit', folder_path)

        try:
            problem = Problem.objects.get(pk=p_id)
        except Problem.DoesNotExist:
            messages.error(request, 'To zadanie nie istnieje.')
            return redirect('folder:edit', folder_path)
        if f.problem_set.filter(id=problem.id).exists():
            messages.error(request, 'To zadanie jest już dodane.')
            return redirect('folder:edit', folder_path)

        cnt_p_inside_f = f.problem_set.count()
        ProblemPlace.objects.create(
            folder = f,
            problem = problem,
            place = cnt_p_inside_f
        )
        messages.success(request, 'Dodano zadanie!')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class DeleteProblem(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        p_id = request.POST['p_id']
        problem = get_object_or_404(Problem, pk=p_id)
        f.problem_set.remove(problem)
        messages.success(request, 'Usunięto zadanie!')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class EditTags(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        tags = request.POST.getlist('tags[]')
        f.tag_set.clear()
        for tag_id in tags:
            f.tag_set.add(Tag.objects.get(id=tag_id))
        f.save()
        messages.success(request, 'Zmieniono tagi!')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class MoveProblemUp(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        p_id = request.POST['p_id']
        p_down = get_object_or_404(ProblemPlace, folder=f, problem=get_object_or_404(Problem, id=p_id))
        p_up   = get_object_or_404(ProblemPlace, folder=f, place=p_down.place - 1)
        p_down.place -= 1
        p_down.save()
        p_up.place += 1
        p_up.save()
        messages.success(request, 'Przesunięto zadanie!')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class Ranking(generic.View):
    problem_list = []

    def dfs(self, prefix, f):
        if f.parent == None:
            prefix = '~'
        elif prefix:
            prefix += ' / ' + f.pretty_name
        else:
            prefix = f.pretty_name
        problems = []
        for fp in ProblemPlace.objects.filter(folder=f).order_by('place').all():
            problems.append(fp.problem)
        if len(problems) != 0:
            self.problem_list.append((prefix, problems))
        for son in Folder.objects.filter(parent=f).all():
            self.dfs(prefix, son)

    def get(self, request, folder_path):
        f = get_folder(folder_path)
        self.problem_list = []
        self.dfs('', f)
        userlist = set()
        for prefix, problems in self.problem_list:
            for problem in problems:
                for user in problem.claiming_user_set.all():
                    if user not in userlist:
                        userlist.add(user)
        tags = []
        if 'tags[]' in request.GET:
            tags = request.GET.getlist('tags[]')
        if tags:
            new_userlist = []
            for user in userlist:
                found = False
                for tag in tags:
                    if user.tag_set.filter(id=tag).exists():
                        found = True
                        break
                if found:
                    new_userlist.append(user)
            userlist = new_userlist

        table = []
        for user in userlist:
            did = []
            sum = 0
            for prefix, problems in self.problem_list:
                for problem in problems:
                    did.append((
                        bool(problem.claiming_user_set.filter(id=user.id).exists()),
                        bool(problem == problems[0]),
                    ))
                    if did[-1][0]:
                        sum += 1

            row = [(-sum, False), (user.last_name, False), (user.first_name, False)]
            row += did
            table.append(row)
        table.sort()
        for row in table:
            name = row[2][0] + ' ' + row[1][0]
            row[2] = (-row[0][0], False)
            row.pop(0)
            row[0] = (name, False)

        context = get_context(folder_path)
        context['problem_list'] = self.problem_list
        context['table'] = table
        context['selected_tags'] = [Tag.objects.get(id=id) for id in tags]
        return render(request, 'folder/ranking.html', context)

@method_decorator(staff_only, name='dispatch')
class ShowSolution(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        f.show_solution ^= 1
        f.save()
        messages.success(request,
                ('Włączono' if f.show_solution else 'Wyłączono') + ' rozwiązania/hinty/odpowiedzi!')
        return redirect('folder:edit', folder_path)

@method_decorator(staff_only, name='dispatch')
class ShowStats(generic.View):
    def post(self, request, folder_path):
        f = get_folder(folder_path)
        f.show_stats ^= 1
        f.save()
        messages.success(request,
                ('Włączono' if f.show_stats else 'Wyłączono') + ' statystyki!')
        return redirect('folder:edit', folder_path)
