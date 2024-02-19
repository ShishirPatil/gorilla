import { createStore } from 'vuex';
import VuexPersistence from 'vuex-persist';

const vuexLocal = new VuexPersistence({
    storage: window.localStorage,
});

export default createStore({
  state: {
    apiDetails: {},
  },
  mutations: {
    setApiDetails(state, details) {
      state.apiDetails = details;
    }
  },
  actions: {
    updateApiDetails({ commit }, details) {
      commit('setApiDetails', details);
    }
  },
  getters: {
    getApiDetails: (state) => {
      return state.apiDetails;
    }
  },
  plugins: [vuexLocal.plugin],
});