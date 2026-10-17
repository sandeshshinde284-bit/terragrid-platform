const fs = require('fs');
const file = 'src/views/prepare/PreparednessChecklist.vue';
let content = fs.readFileSync(file, 'utf8');

content = content.replace(/<strong>\{\{\s*action\.agency\s*\}\}<\/strong> is responsible for this/g, '<strong>{{ action.agency }}</strong> {{ $t(\'prepare.checklist.responsibleFor\') }}');
content = content.replace(/<p class="checkbox-helper">Check off tasks as your team completes them<\/p>/g, '<p class="checkbox-helper">{{ $t(\'prepare.checklist.markComplete\') }}</p>');
content = content.replace(/:title="`Mark as complete`"/g, ':title="$t(\'prepare.checklist.markComplete\')"');
content = content.replace(/<span class="hero-helper">These are the steps your city should take to prepare for this disaster<\/span>/g, '<span class="hero-helper">{{ $t(\'prepare.checklist.helperDesc\') }}</span>');
content = content.replace(/<strong class="cycling-step-text">Creating action plan for \{\{ selectedCity\?\.city \}\}\.\.\.<\/strong>/g, '<strong class="cycling-step-text">{{ $t(\'prepare.checklist.creatingPlan\') }} {{ selectedCity?.city }}...</strong>');
content = content.replace(/<h3>Unable to create checklist<\/h3>/g, '<h3>{{ $t(\'prepare.checklist.unableToCreate\') }}</h3>');

content = content.replace(/\{\{\s*completionStats\.done\s*\}\}\s*\/\s*\{\{\s*completionStats\.total\s*\}\}\s*action items completed/g, '{{ completionStats.done }} {{ $t(\'prepare.checklist.of\') }} {{ completionStats.total }} {{ $t(\'prepare.checklist.actionItemsCompleted\') }}');
content = content.replace(/<label class="filter-label">Showing tasks from:<\/label>/g, '<label class="filter-label">{{ $t(\'prepare.checklist.showingTasksFrom\') }}</label>');
content = content.replace(/:title="\$t\('prepare\.checklist\.agenciesGroupedByUrgency',\s*'Tasks grouped by urgency level'\)"/g, ':title="$t(\'prepare.checklist.agenciesGroupedByUrgency\')"');

fs.writeFileSync(file, content);
console.log('Template cleaned.');
