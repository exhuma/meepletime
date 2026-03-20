import { defineStore } from 'pinia'
import api from '../api'

export const useCirclesStore = defineStore('circles', {
  state: () => ({
    circles: [],
    currentCircle: null,
    members: [],
    calendar: {},    // keyed by date string (YYYY-MM-DD), value: array of AvailabilityOut
    viability: {},   // keyed by date string (YYYY-MM-DD), value: DayViability object
  }),
  actions: {
    async fetchCircles() {
      const res = await api.get('/circles')
      this.circles = res.data
    },
    async fetchCircle(id) {
      const res = await api.get(`/circles/${id}`)
      this.currentCircle = res.data
    },
    async createCircle(data) {
      const res = await api.post('/circles', data)
      this.circles.push(res.data)
      return res.data
    },
    async fetchMembers(circleId) {
      const res = await api.get(`/circles/${circleId}/members`)
      this.members = res.data
    },
    async fetchCalendar(circleId, startDate, endDate) {
      const res = await api.get(`/circles/${circleId}/availability`, {
        params: { start_date: startDate, end_date: endDate },
      })
      // Convert flat list to dict keyed by local_date string
      const dict = {}
      for (const item of res.data) {
        const key = String(item.local_date)
        if (!dict[key]) dict[key] = []
        dict[key].push(item)
      }
      // Merge into existing calendar (preserve dates outside range)
      this.calendar = { ...this.calendar, ...dict }
    },
    async setAvailability(circleId, date, state) {
      const res = await api.put(`/circles/${circleId}/availability/${date}`, { state })
      const updated = res.data
      if (!this.calendar[date]) this.calendar[date] = []
      const idx = this.calendar[date].findIndex(a => a.user_id === updated.user_id)
      if (idx >= 0) {
        this.calendar[date] = this.calendar[date].map((a, i) => i === idx ? updated : a)
      } else {
        this.calendar[date] = [...(this.calendar[date] || []), updated]
      }
    },
    async deleteAvailability(circleId, date, userId) {
      await api.delete(`/circles/${circleId}/availability/${date}`)
      if (this.calendar[date]) {
        this.calendar[date] = this.calendar[date].filter(a => a.user_id !== userId)
      }
    },
    async fetchViability(circleId, startDate, endDate) {
      const res = await api.get(`/circles/${circleId}/viability`, {
        params: { start_date: startDate, end_date: endDate },
      })
      // Convert list to dict keyed by local_date string
      const dict = {}
      for (const item of res.data) {
        dict[String(item.local_date)] = item
      }
      this.viability = { ...this.viability, ...dict }
    },
    async fetchNotes(circleId, date) {
      const res = await api.get(`/circles/${circleId}/notes/${date}`)
      return res.data
    },
    async addNote(circleId, date, content) {
      const res = await api.post(`/circles/${circleId}/notes/${date}`, { content })
      return res.data
    },
    async joinCircle(inviteToken, pseudonym, can_host_default) {
      const res = await api.post('/circles/join', {
        invite_token: inviteToken,
        pseudonym,
        can_host_default,
      })
      return res.data
    },
  },
})
