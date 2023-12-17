
// var existinguser = document.getElementById("user")

// function click(){
// if (existinguser = true){
//     alert("user already has these account details")
//     return false
// }
// };

// click();








// var modal = document.getElementById("myModal");
// var img = document.getElementById("myImg");
// var modalImg = document.getElementById("img01");
// img.onclick = function(){
//   modal.style.display = "block";
//   modalImg.src = this.src;
// }

// var span = document.getElementsByClassName("close")[0];
// span.onclick = function() { 
//   modal.style.display = "none";
// }
// ;

var modalinto = document.querySelector(".modal");
var imgs = document.querySelectorAll(".userimages");
var modalImg2 = document.querySelector(".modal-content");
var spanit = document.querySelector(".close");

imgs.forEach(function(img) {
    img.onclick = function(){
        modalinto.style.display = "block";
        modalImg2.src = this.src;
    }
});

spanit.onclick = function() { 
    modalinto.style.display = "none";
};
var input = document.querySelector("#phone");
window.intlTelInput(input, {
  // Any options go here
});







// Assuming you have a way to get the user's cash history




// let cashHistory = getUserCashHistory();

// let cashData = {
//     labels: cashHistory.map(entry => entry.date),
//     datasets: [{
//         label: 'User Cash',
//         data: cashHistory.map(entry => entry.cash),
//         fill: false,
//         borderColor: 'rgb(75, 192, 192)',
//         tension: 0.1
//     }]
// };

// let config = {
//     type: 'line',
//     data: cashData,
//     options: {}
// };

// let myChart = new Chart(
//     document.getElementById('myChart'),
//     config
// );






