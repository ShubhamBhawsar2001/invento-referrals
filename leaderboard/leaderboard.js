vm = new Vue({
  el: '#app',
  data: {
    cards: []
  }
})

Vue.component('leaderboard-card', {
  data: function () {
  },
  template: `
    <div class="card">
      Hello!
    </div>
  `
})

fetch('https://tusharsadhwani1.pythonanywhere.com/leaderboard')
  .then(res => res.json())
  .then(data => vm.cards = data.leaderboard)
