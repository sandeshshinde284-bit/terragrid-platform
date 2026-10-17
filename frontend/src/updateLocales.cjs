const fs = require('fs');
const path = require('path');

const updateLocale = (file, addendum) => {
    const fullPath = path.join(__dirname, 'locales', file);
    let content = fs.readFileSync(fullPath, 'utf8');
    const checklistMatch = content.match(/"checklist":\s*\{([\s\S]*?)\},/);
    if (checklistMatch) {
        let replacement = '"checklist": {' + checklistMatch[1] + addendum + '\n    },';
        content = content.replace(checklistMatch[0], replacement);
        fs.writeFileSync(fullPath, content);
    }
};

const enAddendum = ',\n      "helperDesc": "These are the steps your city should take to prepare for this disaster",\n      "creatingPlan": "Creating action plan for",\n      "unableToCreate": "Unable to create checklist",\n      "of": "of",\n      "actionItemsCompleted": "action items completed",\n      "showingTasksFrom": "Showing tasks from:",\n      "agenciesGroupedByUrgency": "Tasks grouped by urgency level",\n      "responsibleFor": "is responsible for this",\n      "markComplete": "Mark as complete"';
const deAddendum = ',\n      "helperDesc": "Dies sind die Schritte, die Ihre Stadt unternehmen sollte, um sich auf diese Katastrophe vorzubereiten",\n      "creatingPlan": "Aktionsplan wird erstellt für",\n      "unableToCreate": "Checkliste konnte nicht erstellt werden",\n      "of": "von",\n      "actionItemsCompleted": "Aktionspunkten abgeschlossen",\n      "showingTasksFrom": "Zeige Aufgaben von:",\n      "agenciesGroupedByUrgency": "Aufgaben nach Dringlichkeit gruppiert",\n      "responsibleFor": "ist hierfür verantwortlich",\n      "markComplete": "Als erledigt markieren"';
const esAddendum = ',\n      "helperDesc": "Estos son los pasos que su ciudad debe seguir para prepararse para este desastre",\n      "creatingPlan": "Creando plan de acción para",\n      "unableToCreate": "No se puede crear la lista de verificación",\n      "of": "de",\n      "actionItemsCompleted": "elementos de acción completados",\n      "showingTasksFrom": "Mostrando tareas de:",\n      "agenciesGroupedByUrgency": "Tareas agrupadas por urgencia",\n      "responsibleFor": "es responsable de esto",\n      "markComplete": "Marcar como completado"';
const frAddendum = ',\n      "helperDesc": "Ce sont les mesures que votre ville devrait prendre pour se préparer à cette catastrophe",\n      "creatingPlan": "Création du plan d\\\'action pour",\n      "unableToCreate": "Impossible de créer la liste de contrôle",\n      "of": "sur",\n      "actionItemsCompleted": "actions terminées",\n      "showingTasksFrom": "Affichage des tâches de :",\n      "agenciesGroupedByUrgency": "Tâches regroupées par urgence",\n      "responsibleFor": "est responsable de cela",\n      "markComplete": "Marquer comme terminé"';
const itAddendum = ',\n      "helperDesc": "Questi sono i passaggi che la tua città dovrebbe intraprendere per prepararsi a questo disastro",\n      "creatingPlan": "Creazione del piano d\\\'azione per",\n      "unableToCreate": "Impossibile creare la lista di controllo",\n      "of": "di",\n      "actionItemsCompleted": "azioni completate",\n      "showingTasksFrom": "Visualizzazione delle attività da:",\n      "agenciesGroupedByUrgency": "Attività raggruppate per urgenza",\n      "responsibleFor": "è responsabile di questo",\n      "markComplete": "Segna come completato"';
const plAddendum = ',\n      "helperDesc": "Oto kroki, które Twoje miasto powinno podjąć, aby przygotować się na tę katastrofę",\n      "creatingPlan": "Tworzenie planu działań dla",\n      "unableToCreate": "Nie można utworzyć listy kontrolnej",\n      "of": "z",\n      "actionItemsCompleted": "działań zakończonych",\n      "showingTasksFrom": "Wyświetlanie zadań z:",\n      "agenciesGroupedByUrgency": "Zadania pogrupowane według pilności",\n      "responsibleFor": "jest za to odpowiedzialny",\n      "markComplete": "Oznacz jako ukończone"';
const svAddendum = ',\n      "helperDesc": "Detta är de åtgärder som din stad bör vidta för att förbereda sig för denna katastrof",\n      "creatingPlan": "Skapar handlingsplan för",\n      "unableToCreate": "Kunde inte skapa checklista",\n      "of": "av",\n      "actionItemsCompleted": "åtgärder slutförda",\n      "showingTasksFrom": "Visar uppgifter från:",\n      "agenciesGroupedByUrgency": "Uppgifter grupperade efter brådska",\n      "responsibleFor": "ansvarar för detta",\n      "markComplete": "Markera som slutförd"';

updateLocale('en.json', enAddendum);
updateLocale('de.json', deAddendum);
updateLocale('es.json', esAddendum);
updateLocale('fr.json', frAddendum);
updateLocale('it.json', itAddendum);
updateLocale('pl.json', plAddendum);
updateLocale('sv.json', svAddendum);

console.log('Locale files updated with missing checklist strings.');
