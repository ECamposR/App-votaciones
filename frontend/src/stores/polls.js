import { defineStore } from 'pinia'
import { createCategory, createPoll, createVoterGroup, deleteCategory, deletePoll, deleteVoterGroup, getPoll, listCategories, listPolls, listVoterGroups, transitionPollStatus, updateCategory, updatePoll, updateVoterGroup } from '../api/polls'

export const usePollsStore = defineStore('polls', {
  state: () => ({
    polls: [],
    currentPoll: null,
    loading: false,
    error: null,
  }),
  actions: {
    async loadPolls() {
      this.loading = true
      this.error = null
      try {
        this.polls = await listPolls()
      } finally {
        this.loading = false
      }
    },
    async loadPoll(id) {
      this.loading = true
      this.error = null
      try {
        this.currentPoll = await getPoll(id)
      } finally {
        this.loading = false
      }
    },
    async createPoll(payload) {
      const poll = await createPoll(payload)
      this.polls = [poll, ...this.polls]
      return poll
    },
    async updatePoll(id, payload) {
      const poll = await updatePoll(id, payload)
      this.currentPoll = poll
      this.polls = this.polls.map((item) => (item.id === poll.id ? poll : item))
      return poll
    },
    async deletePoll(id) {
      await deletePoll(id)
      this.polls = this.polls.filter((item) => item.id !== id)
    },
    async transitionStatus(id, status) {
      const poll = await transitionPollStatus(id, status)
      this.currentPoll = poll
      this.polls = this.polls.map((item) => (item.id === poll.id ? poll : item))
      return poll
    },
    async loadGroups(id) {
      return listVoterGroups(id)
    },
    async loadCategories(id) {
      return listCategories(id)
    },
    async createGroup(id, payload) {
      return createVoterGroup(id, payload)
    },
    async updateGroup(id, groupId, payload) {
      return updateVoterGroup(id, groupId, payload)
    },
    async deleteGroup(id, groupId) {
      return deleteVoterGroup(id, groupId)
    },
    async createCategory(id, payload) {
      return createCategory(id, payload)
    },
    async updateCategory(id, categoryId, payload) {
      return updateCategory(id, categoryId, payload)
    },
    async deleteCategory(id, categoryId) {
      return deleteCategory(id, categoryId)
    },
  },
})
