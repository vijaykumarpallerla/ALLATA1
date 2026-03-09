// Global jobs array to be populated from DB
let jobs = [];

// Reference to DOM container
const jobsGrid = document.getElementById("jobsGrid");

// Function to generate job card HTML
function generateJobCard(job) {
    // Generate initials for company logo placeholder
    const initials = job.company.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();

    return `
        <article class="job-card">
            <div class="job-card-header">
                <div class="job-company-info">
                    <div class="company-logo">${initials}</div>
                    <div class="job-title-container">
                        <h3>${job.title}</h3>
                        <span class="company-name">${job.company}</span>
                    </div>
                </div>
                <button class="job-save" aria-label="Save job" onclick="toggleSave(this)">
                    <i class="far fa-bookmark"></i>
                </button>
            </div>
            
            <div class="job-details">
                <div class="job-detail-badge">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${job.location}</span>
                </div>
                <div class="job-detail-badge">
                    <i class="fas fa-briefcase"></i>
                    <span>${job.type}</span>
                </div>
                <div class="job-detail-badge">
                    <i class="fas fa-money-bill-wave"></i>
                    <span>${job.salary}</span>
                </div>
            </div>
            
            <p class="job-description">
                ${job.description}
            </p>
            
            <div class="job-footer">
                <span class="job-posted-time">Posted ${job.posted}</span>
                <button class="btn btn-primary" onclick="applyJob('${job.title}')">Apply Now</button>
            </div>
        </article>
    `;
}

// Render jobs
function renderJobs(listings = jobs) {
    if (!jobsGrid) return;

    if (listings.length === 0) {
        jobsGrid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);"><h3>No jobs match your selected filters.</h3></div>';
        return;
    }

    jobsGrid.innerHTML = listings.map(job => generateJobCard(job)).join('');
}

// Initial render
document.addEventListener("DOMContentLoaded", async () => {

    // Jobs are entirely filtered and rendered server-side now (SSR)

    // Restore checkbox states from URL on page load
    const params = new URLSearchParams(window.location.search);
    const activeJobTypes = params.get('jobtype') ? params.get('jobtype').split(',') : [];
    const activeWorkModels = params.get('workmodel') ? params.get('workmodel').split(',') : [];

    if (activeJobTypes.length > 0 || activeWorkModels.length > 0) {
        document.querySelectorAll('.filter-group').forEach(group => {
            const title = group.querySelector('h4').textContent.trim();
            const checkboxes = group.querySelectorAll('input[type="checkbox"]');

            checkboxes.forEach(cb => {
                const labelText = cb.parentElement.textContent.trim();
                if (title === 'Job Type' && activeJobTypes.includes(labelText)) {
                    cb.checked = true;
                } else if (title === 'Work Model' && activeWorkModels.includes(labelText)) {
                    cb.checked = true;
                }
            });
        });
    }
    const qParam = params.get('q');
    const locParam = params.get('loc');

    if (qParam) {
        document.getElementById('jobTitle').value = qParam;
    }
    if (locParam) {
        document.getElementById('location').value = locParam;
    }

    // Handle search form submission
    const searchForm = document.getElementById("searchForm");
    if (searchForm) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const jobTitle = document.getElementById('jobTitle').value.trim();
            const location = document.getElementById('location').value.trim();

            const searchParams = new URLSearchParams(window.location.search);

            // Delete old page to reset pagination
            searchParams.delete('page');

            if (jobTitle) {
                searchParams.set('q', jobTitle);
            } else {
                searchParams.delete('q');
            }

            if (location) {
                searchParams.set('loc', location);
            } else {
                searchParams.delete('loc');
            }

            const queryString = searchParams.toString() ? '?' + searchParams.toString() : '';
            window.location.href = window.location.pathname + queryString + '#jobs';
        });
    }

    // Attach listener to Apply Filters button
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }

    // Attach listener to Remove Filters button
    const removeFiltersBtn = document.getElementById('removeFiltersBtn');
    if (removeFiltersBtn) {
        removeFiltersBtn.addEventListener('click', () => {
            window.location.href = window.location.pathname + '#jobs';
        });
    }
});

// --- Filter URL & Search Logic ---
function applyFilters() {
    const filterGroups = document.querySelectorAll('.filter-group');
    let jobTypes = [];
    let workModels = [];

    filterGroups.forEach(group => {
        const title = group.querySelector('h4').textContent.trim();
        const checkedBoxes = Array.from(group.querySelectorAll('input[type="checkbox"]:checked'));
        const values = checkedBoxes.map(cb => cb.parentElement.textContent.trim());

        if (title === 'Job Type') {
            jobTypes = values;
        } else if (title === 'Work Model') {
            workModels = values;
        }
    });

    // Format arrays into comma-separated strings
    const jobTypeStr = jobTypes.join(',');
    const workModelStr = workModels.join(',');

    // Construct the new URL maintaining the path but merging with existing query params
    const queryParams = new URLSearchParams(window.location.search);

    // Clear old filter parameters so unchecking is respected
    queryParams.delete('jobtype');
    queryParams.delete('workmodel');

    // Always reset pagination when changing filters
    queryParams.delete('page');

    if (jobTypeStr) queryParams.set('jobtype', jobTypeStr);
    if (workModelStr) queryParams.set('workmodel', workModelStr);

    // Convert to query string (handles ? automatically, but we append #jobs)
    const queryString = queryParams.toString() ? '?' + queryParams.toString() : '';
    const newUrl = `${window.location.pathname}${queryString}#jobs`;

    // Redirect the browser so the server can generate a secure HTML response
    window.location.href = newUrl;
}

// Interactive functions
window.toggleSave = function (btn) {
    const icon = btn.querySelector('i');
    if (icon.classList.contains('far')) {
        icon.classList.remove('far');
        icon.classList.add('fas');
        btn.style.color = 'var(--primary-color)';
    } else {
        icon.classList.remove('fas');
        icon.classList.add('far');
        btn.style.color = 'var(--text-muted)';
    }
};

window.applyJob = function (title) {
    alert("You have started applying for the '" + title + "' position. Good luck!");
};


// --- Mobile Navigation Toggle ---
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenu = document.getElementById('mobile-menu');
    const navMenu = document.getElementById('nav-menu');

    if (mobileMenu && navMenu) {
        mobileMenu.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Dropdown toggle for mobile
    const dropdownLinks = document.querySelectorAll('.nav-dropdown > .nav-link');
    dropdownLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                e.stopPropagation();
                const parent = link.closest('.nav-dropdown');
                parent.classList.toggle('active');
            }
        });
    });
});
