from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.db import models
from .models import Client, Lien


def login_view(request):
    if request.user.is_authenticated:
        return redirect('liens:dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Connexion réussie!')
            return redirect('liens:dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')

    return render(request, 'liens/dashboard/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Déconnexion réussie!')
    return redirect('liens:login')


@login_required
def dashboard(request):
    search_query = request.GET.get('search', '')
    clients = Client.objects.all()

    if search_query:
        clients = clients.filter(
            models.Q(nom__icontains=search_query) |
            models.Q(code_unique__icontains=search_query)
        )

    clients = clients.order_by('-date_creation')

    context = {
        'clients': clients,
        'total_clients': clients.count(),
        'clients_actifs': clients.filter(actif=True).count(),
        'clients_inactifs': clients.filter(actif=False).count(),
        'search_query': search_query,
    }
    return render(request, 'liens/dashboard/dashboard.html', context)


@login_required
def dashboard_search(request):
    """Vue AJAX pour la recherche en temps réel"""
    search_query = request.GET.get('search', '')
    clients = Client.objects.all()

    if search_query:
        clients = clients.filter(
            models.Q(nom__icontains=search_query) |
            models.Q(code_unique__icontains=search_query)
        )

    clients = clients.order_by('-date_creation')

    # Rendu du tableau HTML
    table_html = render_to_string('liens/dashboard/clients_table.html', {
        'clients': clients,
        'search_query': search_query,
    }, request=request)

    # Statistiques
    total_clients = clients.count()
    clients_actifs = clients.filter(actif=True).count()
    clients_inactifs = total_clients - clients_actifs

    return JsonResponse({
        'table_html': table_html,
        'total_clients': total_clients,
        'clients_actifs': clients_actifs,
        'clients_inactifs': clients_inactifs,
        'search_query': search_query,
    })


@login_required
def client_create(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if nom:
            client = Client.objects.create(nom=nom)
            messages.success(request, f'Client "{nom}" créé avec succès!')
            return redirect('liens:client_detail', pk=client.pk)
        else:
            messages.error(request, 'Le nom du client est obligatoire.')

    return render(request, 'liens/dashboard/client_form.html')


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    liens = client.lien_set.filter(url__startswith='http').order_by('ordre', 'date_creation')
    emails = client.lien_set.filter(url__startswith='mailto:').order_by('ordre', 'date_creation')

    context = {
        'client': client,
        'liens': liens,
        'emails': emails,
        'public_url_absolute': request.build_absolute_uri(client.get_public_url()),
    }
    return render(request, 'liens/dashboard/client_detail.html', context)


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        if nom:
            client.nom = nom
            client.save()
            messages.success(request, f'Profil "{nom}" modifié avec succès!')
        else:
            messages.error(request, 'Le nom du client est obligatoire.')

    return redirect('liens:client_detail', pk=pk)


@login_required
def client_toggle_status(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.actif = not client.actif
    client.save()

    status = "activé" if client.actif else "désactivé"
    messages.success(request, f'Profil de "{client.nom}" {status}.')

    # Rediriger vers le dashboard si on vient du dashboard, sinon vers le détail client
    if 'dashboard' in request.META.get('HTTP_REFERER', ''):
        return redirect('liens:dashboard')
    else:
        return redirect('liens:client_detail', pk=pk)


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        nom = client.nom
        client.delete()
        messages.success(request, f'Client "{nom}" supprimé avec succès!')
        return redirect('liens:dashboard')

    context = {'client': client}
    return render(request, 'liens/dashboard/client_delete.html', context)


@login_required
def lien_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)

    if request.method == 'POST':
        is_email = request.POST.get('is_email') == 'true'

        if is_email:
            # Traitement pour les emails
            email_address = request.POST.get('email_address', '').strip()
            titre = request.POST.get('titre', '').strip()

            if email_address and titre:
                url = 'mailto:' + email_address
                lien = Lien.objects.create(
                    client=client,
                    titre=titre,
                    url=url
                )
                messages.success(request, f'Email "{titre}" ajouté avec succès!')
                return redirect('liens:client_detail', pk=client.pk)
            else:
                messages.error(request, 'L\'adresse email et le titre sont obligatoires.')
        else:
            # Traitement pour les liens classiques
            titre = request.POST.get('titre', '').strip()
            url = request.POST.get('url', '').strip()

            if titre and url:
                # Détection automatique email
                if '@' in url and not url.startswith('mailto:'):
                    url = 'mailto:' + url
                # Lien web classique
                elif not url.startswith(('http://', 'https://', 'mailto:')):
                    url = 'https://' + url

                lien = Lien.objects.create(
                    client=client,
                    titre=titre,
                    url=url
                )
                messages.success(request, f'Lien "{titre}" ajouté avec succès!')
                return redirect('liens:client_detail', pk=client.pk)
            else:
                messages.error(request, 'Le titre et l\'URL sont obligatoires.')

    context = {'client': client}
    return render(request, 'liens/dashboard/lien_form.html', context)


@login_required
def lien_edit(request, pk):
    lien = get_object_or_404(Lien, pk=pk)

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        url = request.POST.get('url', '').strip()

        if titre and url:
            # Détection automatique email pour l'édition
            if '@' in url and not url.startswith('mailto:'):
                url = 'mailto:' + url
            # Lien web classique
            elif not url.startswith(('http://', 'https://', 'mailto:')):
                url = 'https://' + url

            lien.titre = titre
            lien.url = url
            lien.save()
            messages.success(request, f'Lien "{titre}" modifié avec succès!')
            return redirect('liens:client_detail', pk=lien.client.pk)
        else:
            messages.error(request, 'Le titre et l\'URL sont obligatoires.')

    context = {'lien': lien, 'client': lien.client}
    return render(request, 'liens/dashboard/lien_edit.html', context)


@login_required
def lien_delete(request, pk):
    lien = get_object_or_404(Lien, pk=pk)
    client = lien.client

    if request.method == 'POST':
        titre = lien.titre
        lien.delete()
        messages.success(request, f'Lien "{titre}" supprimé avec succès!')
        return redirect('liens:client_detail', pk=client.pk)

    context = {'lien': lien, 'client': client}
    return render(request, 'liens/dashboard/lien_delete.html', context)


def profil_public(request, code_unique):
    try:
        client = Client.objects.get(code_unique=code_unique)
    except Client.DoesNotExist:
        raise Http404("Profil non trouvé")

    # Si le profil est inactif, on affiche quand même la page mais avec un message
    if client.actif:
        liens = client.lien_set.all().order_by('ordre', 'date_creation')
    else:
        liens = []

    context = {
        'client': client,
        'liens': liens,
    }
    return render(request, 'liens/public/profil.html', context)