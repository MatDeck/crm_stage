// Filtre par statut et tri des colonnes du tableau des candidatures.
// L'état est mémorisé dans le navigateur pour survivre aux rechargements (ex. après un changement de statut).
const tableau = document.querySelector(".tableau");

if (tableau) {
    const CLE = "candidatures.affichage";
    const corps = tableau.tBodies[0];
    const lignes = [...corps.rows];  // ordre d'origine : plus récentes d'abord
    const pastilles = document.querySelectorAll("[data-filtre-statut]");
    const entetes = tableau.querySelectorAll("th[data-tri]");
    const aucunResultat = document.getElementById("aucun-resultat");

    const etat = charger();

    function charger() {
        const defaut = {statuts: [], tri: null};
        try {
            return {...defaut, ...JSON.parse(localStorage.getItem(CLE))};
        } catch {
            return defaut;
        }
    }

    function sauver() {
        try {
            localStorage.setItem(CLE, JSON.stringify(etat));
        } catch {
            // Stockage indisponible (navigation privée…) : le filtre marche quand même, sans mémoire.
        }
    }

    function appliquerFiltre() {
        const actifs = new Set(etat.statuts);
        let visibles = 0;
        for (const ligne of lignes) {
            ligne.hidden = actifs.size > 0 && !actifs.has(ligne.dataset.statut);
            if (!ligne.hidden) visibles++;
        }
        pastilles.forEach((p) => {
            const statut = p.dataset.filtreStatut;
            p.classList.toggle("active", statut === "" ? actifs.size === 0 : actifs.has(statut));
        });
        aucunResultat.hidden = visibles > 0;
    }

    function valeur(ligne, colonne) {
        const cellule = ligne.cells[colonne];
        const texte = cellule.dataset.valeur ?? cellule.textContent.trim();
        return texte === "—" ? "" : texte;
    }

    function appliquerTri() {
        entetes.forEach((th) => delete th.dataset.sens);
        if (!etat.tri) {
            corps.append(...lignes);
            return;
        }
        const {colonne, sens} = etat.tri;
        entetes.forEach((th) => {
            if (th.cellIndex === colonne) th.dataset.sens = sens;
        });
        const facteur = sens === "asc" ? 1 : -1;
        const triees = [...lignes].sort((a, b) => {
            const va = valeur(a, colonne);
            const vb = valeur(b, colonne);
            // Les cases vides restent toujours en bas.
            if (!va || !vb) return !va - !vb;
            return facteur * va.localeCompare(vb, "fr", {numeric: true, sensitivity: "base"});
        });
        corps.append(...triees);
    }

    pastilles.forEach((p) => p.addEventListener("click", () => {
        const statut = p.dataset.filtreStatut;
        if (statut === "") {
            etat.statuts = [];
        } else if (etat.statuts.includes(statut)) {
            etat.statuts = etat.statuts.filter((s) => s !== statut);
        } else {
            etat.statuts = [...etat.statuts, statut];
        }
        sauver();
        appliquerFiltre();
    }));

    // Clic sur un en-tête : croissant → décroissant → ordre d'origine.
    entetes.forEach((th) => th.addEventListener("click", () => {
        const colonne = th.cellIndex;
        const sens = etat.tri?.colonne === colonne ? {asc: "desc", desc: null}[etat.tri.sens] : "asc";
        etat.tri = sens ? {colonne, sens} : null;
        sauver();
        appliquerTri();
    }));

    appliquerFiltre();
    appliquerTri();
}