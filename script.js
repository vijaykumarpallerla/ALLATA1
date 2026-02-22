// Dummy job data to display on the portal
const jobs = [
    {
        id: 1,
        title: "Senior Full Stack Engineer",
        company: "TechNova Solutions",
        location: "San Francisco, CA (Hybrid)",
        type: "Full-time",
        experience: "Mid-Senior",
        salary: "$130k - $160k a year",
        posted: "2 hours ago",
        description: "We are looking for a Senior Full Stack Engineer to lead the development of our core web application. Experience with React, Node.js, and PostgreSQL is required."
    },
    {
        id: 2,
        title: "Product Marketing Manager",
        company: "Global Innovations Inc.",
        location: "Remote",
        type: "Full-time",
        experience: "Mid Level",
        salary: "$95k - $120k a year",
        posted: "4 hours ago",
        description: "Drive the go-to-market strategy for our new suite of enterprise tools. Work closely with product and sales teams to ensure a successful launch."
    },
    {
        id: 3,
        title: "UX/UI Designer",
        company: "Creative Form",
        location: "New York, NY",
        type: "Contract",
        experience: "Entry-Mid",
        salary: "$50 - $75 an hour",
        posted: "1 day ago",
        description: "Join our agency to craft beautiful, user-centric interfaces for our diverse client base. Portfolio required."
    },
    {
        id: 4,
        title: "Data Scientist",
        company: "DataDrive AI",
        location: "Seattle, WA (Remote)",
        type: "Full-time",
        experience: "Senior",
        salary: "$140k - $180k a year",
        posted: "2 days ago",
        description: "Help us build the next generation of predictive algorithms. Strong background in Python, PyTorch, and large-scale data processing."
    },
    {
        id: 5,
        title: "DevOps Engineer",
        company: "CloudScale Systems",
        location: "Austin, TX",
        type: "Full-time",
        experience: "Mid Level",
        salary: "$110k - $140k a year",
        posted: "3 days ago",
        description: "Maintain and scale our AWS infrastructure. Experience with Kubernetes, Terraform, and CI/CD pipelines is essential."
    },
    {
        id: 6,
        title: "Customer Success Manager",
        company: "ServicePro",
        location: "Chicago, IL (Hybrid)",
        type: "Full-time",
        experience: "Entry Level",
        salary: "$65k - $80k a year",
        posted: "3 days ago",
        description: "Ensure our enterprise clients get the maximum value from our platform. Excellent communication and problem-solving skills needed."
    }
];

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
function renderJobs() {
    if (!jobsGrid) return;

    jobsGrid.innerHTML = jobs.map(job => generateJobCard(job)).join('');
}

// Initial render
document.addEventListener("DOMContentLoaded", () => {
    renderJobs();

    // Prevent form submission for demo
    const searchForm = document.getElementById("searchForm");
    if (searchForm) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            alert("This is a demo portal. Search functionality will be implemented soon!");
        });
    }
});

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
