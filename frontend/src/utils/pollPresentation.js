const votingTypeLabels = {
  PLURALITY: 'Elegir una opcion',
  RANKED: 'Ranking',
  RATING: 'Escala',
  YES_NO: 'Si / No',
}

const pollStatusLabels = {
  draft: 'Borrador',
  open: 'Abierta',
  closed: 'Cerrada',
}

export const votingTypeOptions = [
  { value: 'PLURALITY', label: votingTypeLabels.PLURALITY },
  { value: 'RANKED', label: votingTypeLabels.RANKED },
  { value: 'RATING', label: votingTypeLabels.RATING },
  { value: 'YES_NO', label: votingTypeLabels.YES_NO },
]

export function getVotingTypeLabel(value) {
  return votingTypeLabels[value] ?? value
}

export function getPollStatusLabel(value) {
  return pollStatusLabels[value] ?? value
}

export function formatWeightPercent(weight) {
  const numericWeight = Number(weight)
  if (Number.isNaN(numericWeight)) return '0%'

  const percent = numericWeight * 100
  return `${Number.isInteger(percent) ? percent : Number(percent.toFixed(1))}%`
}

export function getDashboardNextAction(poll, summary = {}) {
  if (!poll) return 'Revisar'

  if (poll.status === 'draft') {
    if ((summary.groupCount ?? 0) === 0) return 'Agregar grupos'
    if ((summary.categoryCount ?? 0) === 0) return 'Agregar categorias'
    return 'Revisar antes de abrir'
  }

  if (poll.status === 'open') return 'Ver resultados en vivo'
  if (poll.status === 'closed') return 'Descargar reporte'

  return 'Revisar'
}
