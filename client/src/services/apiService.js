import axios from 'axios';
axios.defaults.withCredentials = true;
export default {
  getAgenda() { return axios.get('/api/chat/agenda').then(res => res.data); },
  getTerm(word) { return axios.get(`/api/discussion/terms/${word}`).then(res => res.data); },
  getReview() { return axios.get('/api/chat/review').then(res => res.data); }
};