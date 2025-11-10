// Vérifier l'authentification
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/';
}

// Afficher le nom d'utilisateur
const user = JSON.parse(localStorage.getItem('user') || '{}');
document.getElementById('userName').textContent = user.username || '';

// Fonction de déconnexion
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

let currentTab = 'inbox';
let allUsers = [];

// Changer d'onglet
function switchTab(tab) {
    currentTab = tab;
    
    const inboxTab = document.getElementById('inboxTab');
    const sentTab = document.getElementById('sentTab');
    
    if (tab === 'inbox') {
        inboxTab.className = 'px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium transition-all duration-200 shadow-md';
        sentTab.className = 'px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-all duration-200';
        loadInbox();
    } else {
        sentTab.className = 'px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium transition-all duration-200 shadow-md';
        inboxTab.className = 'px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-all duration-200';
        loadSent();
    }
}

// Charger les messages reçus
async function loadInbox() {
    try {
        const response = await fetch('/api/v1/mail/inbox', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load inbox');
        }
        
        const data = await response.json();
        displayMessages(data.messages);
    } catch (error) {
        console.error('Error loading inbox:', error);
        document.getElementById('messagesContainer').innerHTML = '<p class="text-red-500">Erreur lors du chargement des messages.</p>';
    }
}

// Charger les messages envoyés
async function loadSent() {
    try {
        const response = await fetch('/api/v1/mail/sent', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load sent messages');
        }
        
        const data = await response.json();
        displayMessages(data.messages);
    } catch (error) {
        console.error('Error loading sent messages:', error);
        document.getElementById('messagesContainer').innerHTML = '<p class="text-red-500">Erreur lors du chargement des messages.</p>';
    }
}

// Afficher les messages
function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    
    if (messages && messages.length > 0) {
        container.innerHTML = messages.map(message => {
            const senderName = message.sender?.username || 'Inconnu';
            const recipientNames = message.recipients?.map(r => r.username).join(', ') || 'Inconnu';
            const isUnread = currentTab === 'inbox' && !message.is_read;
            
            return `
                <div class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-all ${isUnread ? 'bg-purple-50 border-purple-200' : ''}" 
                     onclick="viewMessage(${message.id})">
                    <div class="flex justify-between items-start">
                        <div class="flex-1">
                            <div class="flex items-center gap-2">
                                ${isUnread ? '<span class="w-2 h-2 bg-purple-600 rounded-full"></span>' : ''}
                                <h3 class="font-semibold text-lg text-gray-800">${escapeHtml(message.subject)}</h3>
                            </div>
                            <p class="text-sm text-gray-600 mt-1">
                                ${currentTab === 'inbox' ? 'De: ' + escapeHtml(senderName) : 'À: ' + escapeHtml(recipientNames)}
                            </p>
                            <p class="text-gray-700 mt-2">${escapeHtml(message.content.substring(0, 100))}${message.content.length > 100 ? '...' : ''}</p>
                        </div>
                        <div class="text-right ml-4">
                            <p class="text-sm text-gray-600">
                                ${new Date(message.created_at).toLocaleDateString('fr-FR')}
                            </p>
                            ${currentTab === 'sent' ? `
                                <button onclick="event.stopPropagation(); deleteMessage(${message.id})" 
                                        class="mt-2 text-red-500 hover:text-red-700 text-sm">
                                    🗑️ Supprimer
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        container.innerHTML = '<p class="text-gray-500">Aucun message.</p>';
    }
}

// Afficher le détail d'un message
async function viewMessage(messageId) {
    try {
        const response = await fetch(`/api/v1/mail/${messageId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load message');
        }
        
        const message = await response.json();
        
        const senderName = message.sender?.username || 'Inconnu';
        const recipientNames = message.recipients?.map(r => r.username).join(', ') || 'Inconnu';
        
        const modal = document.getElementById('messageModal');
        document.getElementById('modalSubject').textContent = message.subject;
        document.getElementById('modalSender').textContent = senderName;
        document.getElementById('modalRecipients').textContent = recipientNames;
        document.getElementById('modalDate').textContent = new Date(message.created_at).toLocaleString('fr-FR');
        document.getElementById('modalContent').textContent = message.content;
        
        modal.classList.remove('hidden');
        
        // Recharger la liste pour mettre à jour le statut "lu"
        if (currentTab === 'inbox') {
            setTimeout(loadInbox, 500);
        }
    } catch (error) {
        console.error('Error loading message:', error);
        alert('Erreur lors du chargement du message.');
    }
}

// Fermer le modal
function closeMessageModal() {
    document.getElementById('messageModal').classList.add('hidden');
}

// Ouvrir le modal de composition
async function openComposeModal() {
    await loadUsers();
    document.getElementById('composeModal').classList.remove('hidden');
}

// Fermer le modal de composition
function closeComposeModal() {
    document.getElementById('composeModal').classList.add('hidden');
    document.getElementById('composeForm').reset();
}

// Charger la liste des utilisateurs
async function loadUsers() {
    try {
        const response = await fetch('/api/v1/users', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load users');
        }
        
        const data = await response.json();
        allUsers = data.users || [];
        
        const select = document.getElementById('recipientSelect');
        select.innerHTML = allUsers
            .filter(u => u.id !== user.id)
            .map(u => `<option value="${u.id}">${escapeHtml(u.username)} (${escapeHtml(u.email)})</option>`)
            .join('');
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Envoyer un message
async function sendMessage(event) {
    event.preventDefault();
    
    const subject = document.getElementById('messageSubject').value;
    const content = document.getElementById('messageContent').value;
    const recipientSelect = document.getElementById('recipientSelect');
    const recipients = Array.from(recipientSelect.selectedOptions).map(opt => parseInt(opt.value));
    
    if (!subject || !content || recipients.length === 0) {
        alert('Veuillez remplir tous les champs et sélectionner au moins un destinataire.');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/mail/send', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                subject,
                content,
                recipients
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to send message');
        }
        
        alert('Message envoyé avec succès !');
        closeComposeModal();
        
        // Recharger les messages
        if (currentTab === 'sent') {
            loadSent();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Erreur lors de l\'envoi du message: ' + error.message);
    }
}

// Supprimer un message
async function deleteMessage(messageId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/mail/${messageId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete message');
        }
        
        alert('Message supprimé avec succès !');
        loadSent();
    } catch (error) {
        console.error('Error deleting message:', error);
        alert('Erreur lors de la suppression du message.');
    }
}

// Échapper HTML pour éviter XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Charger la boîte de réception au chargement
loadInbox();
