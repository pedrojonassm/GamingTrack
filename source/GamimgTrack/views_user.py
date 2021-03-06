from django.shortcuts import render, redirect
from .forms_user import RegisterUserForm, LoginUserForm, ChangeUserPasswordForm, ChangeUserEmailForm, ChangeUserNameForm
from django.http import JsonResponse
from .forms_postagens import CriarPostagemForm

from .models import User, Postagem, Amizade, ConviteAmizade

### Setando strings:
IrParaLogin = "user/login.html"
IrParaRegistrar = "user/register.html"
IrParaInfo = "user/info.html"
IrParaAlterar = "user/alterar.html"
IrParaListarUsers = "user/lista_users.html"
IrParaVisita = "user/visitar_outro.html"
IrParaInicio = "inicio.html"
pedidos_amizade = "user/pedidos_de_amizade.html"
MensagemErro = "Algo de errado não está certo"

IrParaListarPostagens = "posts/lista_postagens.html"
ver_postagem = "posts/ver_postagem.html"
editar_postagem = "posts/editar_post.html"

def RegisterUser(response):
    if response.method == "POST":
        form = RegisterUserForm(response.POST)

        if form.is_valid():
            #create(first_name="Bruce", last_name="Springsteen")
            n = form.cleaned_data["nome"] # n recebe o nome do usuario
            em = form.cleaned_data["email"]
            lo = form.cleaned_data["login"]
            p = form.cleaned_data["password"]
            p1 = form.cleaned_data["password1"]
            r = criar_conta(n, em, lo, p, p1)
            if r == 0:
                return JsonResponse(data = {"message": "Erro: Senhas diferentes"})
            elif r == 1:
                User.objects.create(email=em, login=lo, password=p, nome=n)
                form = LoginUserForm()
                return render(response, IrParaLogin, {"form":form})
            else:
                return JsonResponse(data = {"message": "E-mail já registrado no site"})

    else:
        form = RegisterUserForm()
        return render(response, IrParaRegistrar, {"form":form})

def criar_conta(nome, email, login, senha, repetir_senha):
    if senha != repetir_senha:
        return 0 # Senhas diferentes
    if User.objects.filter(login=login).count() == 0 and User.objects.filter(email=email).count() == 0:
        return 1 # tudo certo, usuário criado
    else:
        return 2 # E-mail ou login já registrado
def LoginUser(response):

    if response.method == "POST":
        form = LoginUserForm(response.POST)

        if form.is_valid():
            lo = form.cleaned_data["login"]
            p = form.cleaned_data["password"]
            if User.objects.filter(login=lo).count() == 0:
                    return JsonResponse(data = {"message": "E-mail não registrado no site"})
            if User.objects.filter(login=lo, password=p).count() == 0:
                return JsonResponse(data = {"message": "Login ou senha incorretos"})
            else:
                logado = User.objects.get(login=lo, password=p)
                response.session['id_user'] = logado.id
                return render(response, IrParaInicio, {"user":logado})
    else:
        form = LoginUserForm()
        return render(response, IrParaLogin, {"form":form})

def mostrar_detalhes(response):
    logado = User.objects.get(id = response.session['id_user'])
    return render(response, IrParaInfo, {"user":logado})

def AlterarSenhaUser(response):
    logado = User.objects.get(id = response.session['id_user'])
    if response.method == "POST":
        form = ChangeUserPasswordForm(response.POST)

        if form.is_valid():
            p = form.cleaned_data["password"]
            p1 = form.cleaned_data["password1"]
            p2 = form.cleaned_data["password2"]
            if (logado.password == p2) and (p == p1):
                logado.password = p
                logado.save()
                return render(response, IrParaInfo, {"user":logado})
            else:
                return JsonResponse(data = {"message": MensagemErro})
    else:
        form = ChangeUserPasswordForm()
        return render(response, IrParaAlterar, {"form":form})

def AlterarNomeUser(response):
    logado = User.objects.get(id = response.session['id_user'])
    if response.method == "POST":
        form = ChangeUserNameForm(response.POST)

        if form.is_valid():
            n = form.cleaned_data['nome']
            p = form.cleaned_data['password']
            if (logado.password == p):
                logado.nome = n
                logado.save()
                return render(response, IrParaInfo, {"user":logado})
            else:
                return JsonResponse(data = {"message": "Senha incorreta"})
    else:
        form = ChangeUserNameForm()
        return render(response, IrParaAlterar, {"form":form})

def AlterarLoginUser(response):
    logado = User.objects.get(id = response.session['id_user'])
    if response.method == "POST":
        form = ChangeUserEmailForm(response.POST)

        if form.is_valid():
            p = form.cleaned_data["password"]
            e = form.cleaned_data['email']
            if (logado.password == p):
                logado.email = e
                logado.save()
                return render(response, IrParaInfo, {"user":logado})
            else:
                return JsonResponse(data = {"message": MensagemErro})
    else:
        form = ChangeUserEmailForm()
        return render(response, IrParaAlterar, {"form":form})

def DeletarMinhaConta(response):
    logado = User.objects.get(id = response.session['id_user'])
    if response.method == "POST":
        form = ChangeUserEmailForm(response.POST)

        if form.is_valid():
            em = form.cleaned_data["email"]
            p = form.cleaned_data["password"]
            if (logado.password == p) and (logado.email == em):
                logado.delete()
                form = LoginUserForm()
                return render(response, IrParaLogin, {"form":form})
            else:
                return JsonResponse(data = {"message": MensagemErro})
    else:
        form = ChangeUserEmailForm()
        return render(response, IrParaAlterar, {"form":form})

def upgradar_conta(logado, ContaParaUpgradar, NivelPermissao):
    if logado.permissionlevel >= NivelPermissao and ContaParaUpgradar.permissionlevel <= logado.permissionlevel and logado.permissionlevel >= 3:
        ContaParaUpgradar.permissionlevel = NivelPermissao
        ContaParaUpgradar.save()
        return 1
    return 0

def ListarUsuarios(response):
    logado = User.objects.get(id = response.session['id_user'])
    if response.method == 'POST':
        # Verifica se foi apertado um botão para upgradar alguma conta
        upgradar = ["Comum", '[criar novo cargo]',"Tutor", "Moderador", "Administrador"] # Lista para os botões de upgrade
        NivelPermissao = 1
        for k in upgradar:
            if k in response.POST:
                ContaParaUpgradar = User.objects.get(id = response.session['id_visita'])
                if upgradar_conta(logado, ContaParaUpgradar, NivelPermissao) == 1:
                    return render(response, IrParaVisita, {"user":logado, "visita":ContaParaUpgradar, "upgradar": upgradar, "amizade": verificar_amizade(logado, ContaParaUpgradar)})
                else:
                    return JsonResponse(data = {"message": MensagemErro})
            NivelPermissao+=1

        # Verifica se o botão pressionado foi o botão de Pesquisar
        if "pesquisar" in response.POST:
            lista = []
            filtro = response.POST.get('filtro')
            for users in User.objects.filter(nome__contains=filtro):
                sla = []
                sla.append(users.nome)
                sla.append(users.id)
                lista.append(sla)
                # Ele filtra pela pesquisa por nome
            return render(response, IrParaListarUsers, {'lista': lista})
        for i in User.objects.all():
            if str(i.id) in response.POST:
                # Aqui ele verifica se o botão pressionado tem o id do user na resposta do select
                if i == logado:
                    return render(response, IrParaInfo, {"user":logado})
                visitar = i
                response.session['id_visita'] = visitar.id
                return render(response, IrParaVisita, {"user":logado, "visita":visitar, "upgradar": upgradar, "amizade": verificar_amizade(logado, visitar)})

        return JsonResponse(data = {"message": MensagemErro})
    else:
        lista = []
        for users in User.objects.all():
            sla = []
            sla.append(users.nome)
            sla.append(users.id)
            lista.append(sla)
            #lista recebe uma lista que possue sempre 2 valores, o primeiro é o nome do usuario e o segundo o seu id, que ficará no nome do botão
        return render(response, IrParaListarUsers, {'lista': lista})

def ApagarOutraConta(response):
    # Adm pode apagar uma conta de outro usuario
    logado = User.objects.get(id = response.session['id_user'])
    ContaParaDeletar = User.objects.get(id = response.session['id_visita'])
    k = deletar_outra_conta(logado.permissionlevel, ContaParaDeletar.permissionlevel)
    if k == 1:
        ContaParaDeletar.delete()
        response.session['id_visita'] = ''
        return render(response, IrParaInicio, {"user":logado})
    else:
        return JsonResponse(data = {"message": MensagemErro})

def deletar_outra_conta(nivel_de_permissao_logado, nivel_de_permissao_da_conta_a_ser_deletada):
    if nivel_de_permissao_logado >= 4 and nivel_de_permissao_da_conta_a_ser_deletada <= nivel_de_permissao_logado:
        return 1
    else:
        return 0

def mostrar_meus_posts(response):
    logado = User.objects.get(id = response.session['id_user'])
    lista = []
    if response.method == "POST":
        if "editar_post" in response.POST:
            post = Postagem.objects.get(id = response.session['id_postagem'])
            form = CriarPostagemForm(initial={'content': post.content, 'title': post.title})
            return render(response, editar_postagem, {"form":form})
        elif "save_post" in response.POST:
            visitar = Postagem.objects.get(id = response.session['id_postagem'])
            form = CriarPostagemForm(response.POST)
            if form.is_valid():
                criador = visitar.user_criador
                visitar.content = form.cleaned_data['content']
                visitar.title = form.cleaned_data['title']
                visitar.save()
                return render(response, ver_postagem, {"user":logado, "post":visitar, "criador": criador})
        for i in Postagem.objects.all():
            if str(i.id) in response.POST:
                # Aqui ele verifica se o botão pressionado tem o id do user no select
                visitar = i
                response.session['id_postagem'] = visitar.id
                criador = visitar.user_criador
                return render(response, ver_postagem, {"user":logado, "post":visitar, "criador": criador})
        filtro = response.POST.get('filtro')
        for posts in Postagem.objects.filter(user_criador = logado, title__contains=filtro):
            sla = []
            sla.append(posts.title)
            sla.append(posts.id)
            lista.append(sla)
        return render(response, IrParaListarPostagens, {'lista': lista})
    for posts in Postagem.objects.filter(user_criador = logado):
        sla = []
        sla.append(posts.title)
        sla.append(posts.id)
        lista.append(sla)
    return render(response, IrParaListarPostagens, {'lista': lista})

# Amizade
def verificar_amizade(logado, visita):
#    Retorna:
#        1 se eles são amigos
#        2 se existe um pedido de amizade do logado para o user que ele está visitando
#        3 se existe um pedido de amizade do user que o usuário logado está visitando para ele
#        0 caso não exista nada
    if Amizade.objects.filter(amigo=logado, amigo2=visita).count() == 1 or Amizade.objects.filter(amigo=visita, amigo2=logado).count() == 1:
        return 1
    elif ConviteAmizade.objects.filter(quem_enviou=logado, quem_recebeu_o_pedido=visita).count() == 1:
        return 2
    elif ConviteAmizade.objects.filter(quem_enviou=visita, quem_recebeu_o_pedido=logado).count() == 1:
        return 3
    else:
        return 0

def adicionar_amigo(response):
    logado = User.objects.get(id = response.session['id_user'])
    visita = User.objects.get(id = response.session['id_visita'])
    upgradar = ["Comum", '[criar novo cargo]',"Tutor", "Moderador", "Administrador"] # Lista para os botões de upgrade
    if response.method == "POST":
        if "adicionar" in response.POST: # verifica se foi pressionado o botão de adicionar amigo
            ConviteAmizade.objects.create(quem_enviou=logado, quem_recebeu_o_pedido=visita).save() # cria a amizade
        if "excluir" in response.POST:
            if Amizade.objects.filter(amigo=logado, amigo2=visita).count() == 1:
                Amizade.objects.get(amigo=logado, amigo2=visita).delete()
            else:
                Amizade.objects.get(amigo=visita, amigo2=logado).delete()
        elif "cancelar" in response.POST:
            ConviteAmizade.objects.get(quem_enviou=logado, quem_recebeu_o_pedido=visita).delete()
        elif "aceitar" in response.POST:
            ConviteAmizade.objects.get(quem_enviou=visita, quem_recebeu_o_pedido=logado).delete()
            Amizade.objects.create(amigo=logado, amigo2=visita).save()
        elif "recusar" in response.POST:
            ConviteAmizade.objects.get(quem_enviou=visita, quem_recebeu_o_pedido=logado).delete()
        return render(response, IrParaVisita, {"user":logado, "visita":visita, "upgradar": upgradar, "amizade": verificar_amizade(logado, visita)})
    return JsonResponse(data = {"message": MensagemErro})

def ver_pedidos_de_amizade(response):
    logado = User.objects.get(id = response.session['id_user'])
    upgradar = ["Comum", '[criar novo cargo]',"Tutor", "Moderador", "Administrador"] # Lista para os botões de upgrade
    if response.method == "POST":
        # Para chegar aqui ele precisa primeiro ver a lista de amizades, logo, para poupar tempo, verificamos se existe apenas os id's dos users que o pediram em amizade:
        for i in ConviteAmizade.objects.filter(quem_recebeu_o_pedido=logado):
            if str(i.quem_enviou.id) in response.POST:
                response.session['id_visita'] = i.quem_enviou.id
                return render(response, IrParaVisita, {"user":logado, "visita":i.quem_enviou, "upgradar": upgradar, "amizade": verificar_amizade(logado, i.quem_enviou)})
    else:
        # Lista guarda o nome da pessoa que enviou o convite e o id dela, respectivamente
        lista = []
        for i in ConviteAmizade.objects.filter(quem_recebeu_o_pedido=logado):
            sla = []
            sla.append(i.quem_enviou.nome)
            sla.append(i.quem_enviou.id)
            lista.append(sla)
        return render(response, pedidos_amizade, {"pedidos": lista})
    return JsonResponse(data = {"message": "asdasdas"})