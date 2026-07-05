document.addEventListener('DOMContentLoaded', () => {
    const triageGrid = document.getElementById('triage-grid');
    const pendingCount = document.getElementById('pending-count');
    const toastContainer = document.getElementById('toast-container');

    const TEMPLATES = {
        hazard: "This item is hazardous. Take to the local Hazardous Waste Facility (123 Main St), open every first Saturday.",
        battery: "Do NOT place in general waste or recycling bins. Take to the Central E-Waste Dropoff location.",
        plastics: "Clean and dry all plastic containers. Only plastics labeled #1 and #2 are accepted in the blue bin.",
        cardboard: "Flatten cardboard boxes. Greasy cardboard (like pizza boxes) must go in general waste or compost."
    };

    // Helper: Show custom toast notification
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type === 'error' ? 'error' : ''}`;
        
        const iconName = type === 'error' ? 'alert-triangle' : 'check-circle';
        toast.innerHTML = `
            <i data-feather="${iconName}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        feather.replace();

        // Auto remove toast
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px) scale(0.95)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    async function fetchPendingItems() {
        try {
            const response = await fetch('/api/v1/admin/pending');
            const items = await response.json();
            
            pendingCount.textContent = `${items.length} Pending`;
            renderItems(items);
        } catch (error) {
            console.error("Failed to fetch pending items:", error);
            triageGrid.innerHTML = '<p style="color: var(--danger)">Error loading triage queue.</p>';
            showToast("Failed to load triage items", "error");
        }
    }

    function renderItems(items) {
        triageGrid.innerHTML = '';
        
        if (items.length === 0) {
            triageGrid.innerHTML = '<p style="color: var(--text-secondary); grid-column: 1/-1; text-align: center; padding: 5rem 0; font-size: 1.1rem;">Queue is empty! All items resolved. 🎉</p>';
            return;
        }

        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'triage-card';
            card.id = `card-${item.id}`;
            
            let imageHtml = '';
            if (item.image_url) {
                imageHtml = `<img src="${item.image_url}" class="card-image" alt="Waste Item" onerror="this.style.display='none'">`;
            }

            // Extract AI Draft if present in agent_notes
            let cleanNotes = item.agent_notes || '';
            let aiDraft = '';
            const draftMatch = cleanNotes.match(/\[AI Draft:\s*(.*?)\]/);
            if (draftMatch) {
                aiDraft = draftMatch[1].trim();
                // Strip the draft from notes for cleaner display
                cleanNotes = cleanNotes.replace(/\[AI Draft:\s*.*?\]/, '').trim();
            }

            let aiSuggestionHtml = '';
            if (aiDraft) {
                aiSuggestionHtml = `
                    <div class="ai-suggestion-box">
                        <div class="ai-suggestion-title">
                            <i data-feather="cpu" style="width: 14px; height: 14px;"></i>
                            AI Suggested Resolution
                        </div>
                        <div class="ai-suggestion-text">"${aiDraft}"</div>
                        <button class="use-suggestion-btn" onclick="useSuggestion(${item.id}, \`${aiDraft.replace(/`/g, '\\`').replace(/"/g, '&quot;')}\`)">
                            Accept AI Draft
                        </button>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="card-header">
                    <span class="card-id">#ID-${item.id}</span>
                    <span class="card-status">${item.status}</span>
                </div>
                <div class="card-body">
                    ${imageHtml}
                    <div class="card-query">"${item.user_query}"</div>
                    <div class="card-notes">${cleanNotes || 'Flagged for review.'}</div>
                    ${aiSuggestionHtml}
                </div>
                <div class="card-footer">
                    <textarea class="resolve-input" id="resolve-text-${item.id}" placeholder="Provide correct disposal instructions to the user..."></textarea>
                    
                    <div class="templates-bar">
                        <button class="template-btn" onclick="applyTemplate(${item.id}, 'hazard')">☣️ Hazard</button>
                        <button class="template-btn" onclick="applyTemplate(${item.id}, 'battery')">🔋 Battery</button>
                        <button class="template-btn" onclick="applyTemplate(${item.id}, 'plastics')">♻️ Plastics</button>
                        <button class="template-btn" onclick="applyTemplate(${item.id}, 'cardboard')">📦 Cardboard</button>
                    </div>

                    <button class="resolve-btn" onclick="resolveItem(${item.id})">Mark as Resolved</button>
                </div>
            `;
            
            triageGrid.appendChild(card);
        });

        feather.replace();
    }

    // Interactive functions exposed to window
    window.useSuggestion = function(id, text) {
        const textarea = document.getElementById(`resolve-text-${id}`);
        if (textarea) {
            textarea.value = text;
            showToast("AI Draft applied!");
        }
    };

    window.applyTemplate = function(id, key) {
        const textarea = document.getElementById(`resolve-text-${id}`);
        if (textarea && TEMPLATES[key]) {
            textarea.value = TEMPLATES[key];
            showToast(`Template '${key}' applied!`);
        }
    };

    window.resolveItem = async function(id) {
        const textarea = document.getElementById(`resolve-text-${id}`);
        const resolutionText = textarea ? textarea.value.trim() : '';
        
        if (!resolutionText) {
            showToast("Please enter resolution instructions.", "error");
            return;
        }

        try {
            const response = await fetch(`/api/v1/admin/resolve/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ admin_resolution: resolutionText })
            });

            if (response.ok) {
                // Fade out animation
                const card = document.getElementById(`card-${id}`);
                if (card) {
                    card.classList.add('fade-out');
                }
                showToast(`Item #ID-${id} resolved successfully!`);
                
                // Wait for animation to finish before updating grid
                setTimeout(fetchPendingItems, 400);
            } else {
                showToast("Failed to resolve item.", "error");
            }
        } catch (error) {
            console.error("Resolution Error:", error);
            showToast("Network error.", "error");
        }
    };

    // Initial fetch
    fetchPendingItems();
});
