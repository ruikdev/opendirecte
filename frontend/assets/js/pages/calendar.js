// Vérifier l'authentification
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/';
}

// Afficher le nom d'utilisateur
const user = JSON.parse(localStorage.getItem('user') || '{}');
document.getElementById('userName').textContent = user.username || '';

// Afficher les actions pour prof/admin
if (user.role === 'prof' || user.role === 'admin') {
    document.getElementById('teacherActions').classList.remove('hidden');
}

// Variables globales
let currentWeekOffset = 0;
let allEvents = [];
let allGroups = [];

// Fonction de déconnexion
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Charger les groupes de l'utilisateur
async function loadGroups() {
    try {
        const response = await fetch('/api/v1/groups', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            allGroups = data.groups || [];
            console.log('Groupes chargés:', allGroups); // Debug
            populateGroupSelect();
        } else {
            console.error('Erreur lors du chargement des groupes:', response.status);
        }
    } catch (error) {
        console.error('Error loading groups:', error);
    }
}

// Remplir le select des groupes
function populateGroupSelect() {
    const select = document.getElementById('courseGroup');
    select.innerHTML = '';
    
    console.log('Remplissage du select avec', allGroups.length, 'groupes'); // Debug
    
    if (allGroups.length === 0) {
        select.innerHTML = '<option value="" disabled>Aucun groupe disponible - Contactez un administrateur</option>';
        return;
    }
    
    allGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        select.appendChild(option);
    });
}

// Charger les événements du calendrier
async function loadEvents() {
    try {
        const response = await fetch('/api/v1/calendar', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load events');
        }
        
        const data = await response.json();
        allEvents = data.events || [];
        renderWeekView();
    } catch (error) {
        console.error('Error loading events:', error);
        document.getElementById('calendarContainer').innerHTML = '<p class="text-red-500">Erreur lors du chargement du calendrier.</p>';
    }
}

// Obtenir le début de la semaine
function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Lundi
    return new Date(d.setDate(diff));
}

// Changer de semaine
function changeWeek(offset) {
    currentWeekOffset += offset;
    renderWeekView();
}

// Aller à aujourd'hui
function goToToday() {
    currentWeekOffset = 0;
    renderWeekView();
}

// Afficher la vue hebdomadaire
function renderWeekView() {
    const today = new Date();
    const weekStart = getWeekStart(today);
    weekStart.setDate(weekStart.getDate() + (currentWeekOffset * 7));
    
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekEnd.getDate() + 6);
    
    // Mettre à jour l'affichage de la semaine
    const weekDisplay = document.getElementById('weekDisplay');
    weekDisplay.textContent = `Semaine du ${weekStart.toLocaleDateString('fr-FR')} au ${weekEnd.toLocaleDateString('fr-FR')}`;
    
    // Filtrer les événements de la semaine
    const weekEvents = allEvents.filter(event => {
        const eventDate = new Date(event.start_time);
        return eventDate >= weekStart && eventDate <= weekEnd;
    });
    
    // Générer la grille
    const container = document.getElementById('calendarContainer');
    const days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
    const hours = Array.from({ length: 14 }, (_, i) => i + 7); // 7h à 20h
    
    let html = '<div class="overflow-x-auto">';
    html += '<table class="w-full border-collapse">';
    html += '<thead><tr><th class="border p-2 bg-gray-50 w-20">Heure</th>';
    
    // En-têtes des jours
    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(weekStart);
        dayDate.setDate(dayDate.getDate() + i);
        const isToday = dayDate.toDateString() === today.toDateString();
        html += `<th class="border p-2 ${isToday ? 'bg-orange-100' : 'bg-gray-50'} min-w-[140px]">
            <div class="font-semibold">${days[i]}</div>
            <div class="text-sm font-normal">${dayDate.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}</div>
        </th>`;
    }
    html += '</tr></thead><tbody>';
    
    // Lignes des heures
    hours.forEach(hour => {
        html += '<tr>';
        html += `<td class="border p-2 text-sm text-gray-600 bg-gray-50 text-center font-medium">${hour}:00</td>`;
        
        for (let i = 0; i < 7; i++) {
            const dayDate = new Date(weekStart);
            dayDate.setDate(dayDate.getDate() + i);
            
            // Trouver les événements pour cette cellule
            const cellEvents = weekEvents.filter(event => {
                const eventDate = new Date(event.start_time);
                const eventHour = eventDate.getHours();
                return eventDate.toDateString() === dayDate.toDateString() && 
                       eventHour === hour;
            });
            
            html += '<td class="border p-1 align-top time-slot">';
            cellEvents.forEach(event => {
                html += renderEventCard(event);
            });
            html += '</td>';
        }
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    if (weekEvents.length === 0) {
        html += '<div class="text-center py-8 text-gray-500">Aucun cours cette semaine</div>';
    }
    
    container.innerHTML = html;
}

// Rendre une carte d'événement
function renderEventCard(event) {
    const startDate = new Date(event.start_time);
    const endDate = new Date(event.end_time);
    const isPast = endDate < new Date();
    const canEdit = user.role === 'prof' || user.role === 'admin';
    
    const duration = (endDate - startDate) / (1000 * 60); // en minutes
    const heightClass = duration > 60 ? 'min-h-[120px]' : 'min-h-[60px]';
    
    return `
        <div class="mb-1 p-2 rounded-lg border-l-4 ${isPast ? 'bg-gray-100 border-gray-400' : 'bg-orange-50 border-orange-500'} ${heightClass} hover:shadow-md transition-shadow cursor-pointer" onclick="viewEventDetails(${event.id})">
            <div class="font-semibold text-sm text-gray-800 mb-1">${escapeHtml(event.title)}</div>
            <div class="text-xs text-gray-600">
                ${startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                - ${endDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            </div>
            ${event.location ? `<div class="text-xs text-gray-600 mt-1">📍 ${escapeHtml(event.location)}</div>` : ''}
            ${event.group_name ? `<div class="text-xs text-gray-500 mt-1">${escapeHtml(event.group_name)}</div>` : ''}
            ${event.parent_event_id ? '<div class="text-xs text-orange-600 mt-1">🔁 Récurrent</div>' : ''}
        </div>
    `;
}

// Voir les détails d'un événement
function viewEventDetails(eventId) {
    const event = allEvents.find(e => e.id === eventId);
    if (!event) return;
    
    const startDate = new Date(event.start_time);
    const endDate = new Date(event.end_time);
    const canEdit = user.role === 'prof' && event.created_by === user.id;
    const canDelete = canEdit;
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    modal.innerHTML = `
        <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full animate-slide-in">
            <div class="bg-gradient-to-r from-orange-500 to-orange-600 p-6 text-white rounded-t-2xl">
                <h2 class="text-2xl font-bold">${escapeHtml(event.title)}</h2>
                ${event.creator_name ? `<p class="text-sm mt-1 text-orange-100">Par ${escapeHtml(event.creator_name)}</p>` : ''}
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <div class="text-sm font-semibold text-gray-500 mb-1">Date et heure</div>
                    <div class="text-gray-800">
                        ${startDate.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
                    </div>
                    <div class="text-gray-800">
                        ${startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                        - ${endDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                </div>
                
                ${event.group_name ? `
                <div>
                    <div class="text-sm font-semibold text-gray-500 mb-1">Classe</div>
                    <div class="text-gray-800">${escapeHtml(event.group_name)}</div>
                </div>` : ''}
                
                ${event.location ? `
                <div>
                    <div class="text-sm font-semibold text-gray-500 mb-1">Salle</div>
                    <div class="text-gray-800">📍 ${escapeHtml(event.location)}</div>
                </div>` : ''}
                
                ${event.description ? `
                <div>
                    <div class="text-sm font-semibold text-gray-500 mb-1">Description</div>
                    <div class="text-gray-800">${escapeHtml(event.description)}</div>
                </div>` : ''}
                
                ${event.parent_event_id || event.is_recurring ? `
                <div class="bg-orange-50 p-3 rounded-lg">
                    <div class="text-sm font-semibold text-orange-700">🔁 Cours récurrent</div>
                </div>` : ''}
                
                <div class="flex justify-end space-x-3 pt-4 border-t">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors">
                        Fermer
                    </button>
                    ${canDelete ? `
                    <button onclick="deleteCourse(${event.id}, ${event.is_recurring || event.parent_event_id})" class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors">
                        Supprimer
                    </button>` : ''}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Ouvrir le modal d'ajout de cours
function openAddCourseModal() {
    document.getElementById('modalTitle').textContent = 'Ajouter un cours';
    document.getElementById('courseForm').reset();
    document.getElementById('eventId').value = '';
    
    // Définir la date par défaut à aujourd'hui
    const today = new Date();
    document.getElementById('courseDate').valueAsDate = today;
    updateDayName();
    
    document.getElementById('courseModal').classList.remove('hidden');
}

// Fermer le modal
function closeModal() {
    document.getElementById('courseModal').classList.add('hidden');
}

// Mettre à jour le nom du jour
document.getElementById('courseDate').addEventListener('change', updateDayName);

function updateDayName() {
    const dateInput = document.getElementById('courseDate');
    const dayNameInput = document.getElementById('courseDayName');
    
    if (dateInput.value) {
        const date = new Date(dateInput.value + 'T12:00:00');
        const dayName = date.toLocaleDateString('fr-FR', { weekday: 'long' });
        dayNameInput.value = dayName.charAt(0).toUpperCase() + dayName.slice(1);
    } else {
        dayNameInput.value = '';
    }
}

// Gérer la case à cocher récurrence
document.getElementById('isRecurring').addEventListener('change', function() {
    const recurringOptions = document.getElementById('recurringOptions');
    if (this.checked) {
        recurringOptions.classList.remove('hidden');
        // Définir une date de fin par défaut (3 mois)
        const endDate = new Date();
        endDate.setMonth(endDate.getMonth() + 3);
        document.getElementById('recurrenceEnd').valueAsDate = endDate;
    } else {
        recurringOptions.classList.add('hidden');
    }
});

// Soumettre le formulaire
document.getElementById('courseForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const eventId = document.getElementById('eventId').value;
    const title = document.getElementById('courseTitle').value;
    const groupSelect = document.getElementById('courseGroup');
    const selectedOptions = Array.from(groupSelect.selectedOptions);
    const groupIds = selectedOptions.map(opt => parseInt(opt.value));
    const date = document.getElementById('courseDate').value;
    const startTime = document.getElementById('courseStartTime').value;
    const endTime = document.getElementById('courseEndTime').value;
    const location = document.getElementById('courseLocation').value;
    const description = document.getElementById('courseDescription').value;
    const isRecurring = document.getElementById('isRecurring').checked;
    const recurrenceType = document.getElementById('recurrenceType').value;
    const recurrenceEnd = document.getElementById('recurrenceEnd').value;
    
    // Validation
    if (!title || groupIds.length === 0 || !date || !startTime || !endTime) {
        alert('Veuillez remplir tous les champs obligatoires et sélectionner au moins une classe');
        return;
    }
    
    // Construire les dates ISO
    const startDateTime = `${date}T${startTime}:00`;
    const endDateTime = `${date}T${endTime}:00`;
    
    const data = {
        title,
        group_ids: groupIds,
        start_time: startDateTime,
        end_time: endDateTime,
        location,
        description,
        is_recurring: isRecurring,
        recurrence_type: isRecurring ? recurrenceType : null,
        recurrence_end: isRecurring && recurrenceEnd ? `${recurrenceEnd}T23:59:59` : null
    };
    
    try {
        const url = eventId ? `/api/v1/calendar/${eventId}` : '/api/v1/calendar';
        const method = eventId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            closeModal();
            await loadEvents(); // Recharger les événements
            alert(result.message || 'Cours enregistré avec succès');
        } else {
            alert(result.error || 'Erreur lors de l\'enregistrement');
        }
    } catch (error) {
        console.error('Error saving course:', error);
        alert('Erreur lors de l\'enregistrement du cours');
    }
});

// Supprimer un cours
async function deleteCourse(eventId, isRecurring) {
    let deleteSeries = false;
    
    if (isRecurring) {
        const choice = confirm('Ce cours fait partie d\'une série récurrente.\n\nOK = Supprimer toute la série\nAnnuler = Supprimer uniquement ce cours');
        if (choice === null) return;
        deleteSeries = choice;
    } else {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce cours ?')) {
            return;
        }
    }
    
    try {
        const response = await fetch(`/api/v1/calendar/${eventId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ delete_series: deleteSeries })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Fermer le modal de détails s'il est ouvert
            const detailModal = document.querySelector('.fixed');
            if (detailModal) detailModal.remove();
            
            await loadEvents(); // Recharger les événements
            alert(result.message || 'Cours supprimé avec succès');
        } else {
            alert(result.error || 'Erreur lors de la suppression');
        }
    } catch (error) {
        console.error('Error deleting course:', error);
        alert('Erreur lors de la suppression du cours');
    }
}

// Fonction utilitaire pour échapper le HTML
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Initialisation
document.addEventListener('DOMContentLoaded', async () => {
    await loadGroups();
    await loadEvents();
});
