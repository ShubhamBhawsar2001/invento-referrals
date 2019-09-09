vm = new Vue({
  el: '#app',
  data: {
    cards: []
  }
})

fetch('https://tusharsadhwani1.pythonanywhere.com/leaderboard')
  .then(res => res.json())
  .then(data => vm.cards = data.leaderboard)
