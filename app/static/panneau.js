// Panneau latéral : charge le fragment HTML d'une candidature et l'affiche sur le côté.
const panneau = document.getElementById("panneau");
const voile = document.getElementById("voile");

async function ouvrirPanneau(url) {
    const reponse = await fetch(url);
    if (!reponse.ok) return;
    panneau.innerHTML = await reponse.text();
    panneau.classList.add("ouvert");
    voile.classList.add("visible");
}

function fermerPanneau() {
    panneau.classList.remove("ouvert");
    voile.classList.remove("visible");
    // Retire ?ouvrir=... de l'URL pour qu'un rechargement ne rouvre pas le panneau.
    history.replaceState(null, "", location.pathname);
}

document.addEventListener("click", (e) => {
    if (e.target.closest("[data-fermer]")) return fermerPanneau();
    // Les contrôles dans une ligne (ex. le select de statut) ne doivent pas ouvrir le panneau.
    if (e.target.closest("tr") && e.target.closest("select, button, a, input")) return;
    const declencheur = e.target.closest("[data-panneau]");
    if (declencheur) ouvrirPanneau(declencheur.dataset.panneau);
});

voile.addEventListener("click", fermerPanneau);
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") fermerPanneau();
});

if (panneau.dataset.ouvrir) ouvrirPanneau(panneau.dataset.ouvrir);