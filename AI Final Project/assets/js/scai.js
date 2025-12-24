'use strict';

/* ================= GLOBAL ================= */
let db;
let map;
let markers = [];
let polyline;

/* DOM ELEMENTS */
let username, startCity, budget, days, preference;
let userList, output;

/* ================= DOM READY ================= */
document.addEventListener("DOMContentLoaded", () => {

  username   = document.getElementById("username");
  startCity  = document.getElementById("startCity");
  budget     = document.getElementById("budget");
  days       = document.getElementById("days");
  preference = document.getElementById("preference");
  userList   = document.getElementById("userList");
  output     = document.getElementById("output");

  initDB();
});

/* ================= DATABASE INIT ================= */
async function initDB(){
  const SQL = await initSqlJs({
    locateFile: f =>
      `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${f}`
  });

  db = new SQL.Database();

  db.run(`
    CREATE TABLE users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT,
      start_city TEXT,
      budget INTEGER,
      days INTEGER,
      preference TEXT,
      result TEXT
    );

    CREATE TABLE cities(
      name TEXT,
      daily_cost INTEGER,
      rating INTEGER,
      category TEXT,
      lat REAL,
      lng REAL
    );

    CREATE TABLE distances(
      from_city TEXT,
      to_city TEXT,
      travel_cost INTEGER
    );
  `);

  insertData();
  initMap();
  loadCities();
}

/* ================= INSERT DATA ================= */
function insertData(){
  const categories=["Cultural","Beach","Adventure","Luxury","Historical"];

  const cityNames = [
    ["Paris",48.8566,2.3522],
    ["Rome",41.9028,12.4964],
    ["Cairo",30.0444,31.2357],
    ["Dubai",25.2048,55.2708],
    ["Tokyo",35.6895,139.6917],
    ["New York",40.7128,-74.0060],
    ["London",51.5074,-0.1278],
    ["Barcelona",41.3851,2.1734],
    ["Sydney",-33.8688,151.2093],
    ["Bali",-8.4095,115.1889],
    ["Istanbul",41.0082,28.9784],
    ["Bangkok",13.7563,100.5018],
    ["Singapore",1.3521,103.8198]
  ];

  cityNames.forEach(c=>{
    db.run(
      "INSERT INTO cities VALUES (?,?,?,?,?,?)",
      [c[0],100,5,"Cultural",c[1],c[2]]
    );
  });

  for(let i=1;i<=300;i++){
    db.run(
      "INSERT INTO cities VALUES (?,?,?,?,?,?)",
      [
        "City_"+i,
        50+(i%5)*30,
        3+(i%3),
        categories[i%categories.length],
        -50+Math.random()*100,
        -180+Math.random()*360
      ]
    );
  }

  let allCities=db.exec("SELECT name FROM cities")[0].values;
  for(let i=0;i<allCities.length-1;i++){
    db.run(
      "INSERT INTO distances VALUES (?,?,?)",
      [
        allCities[i][0],
        allCities[i+1][0],
        20+Math.floor(Math.random()*50)
      ]
    );
  }
}

/* ================= MAP ================= */
function initMap(){
  map = L.map('map').setView([20,0],2);

  L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    { attribution:'© OpenStreetMap' }
  ).addTo(map);

  drawMarkers();
}

function drawMarkers(){
  markers.forEach(m=>map.removeLayer(m));
  markers=[];

  let cities=db.exec("SELECT * FROM cities")[0].values;
  cities.forEach(c=>{
    markers.push(
      L.marker([c[4],c[5]]).addTo(map).bindPopup(c[0])
    );
  });
}

/* ================= USERS ================= */
function addUser(){
  if(!username.value || !budget.value || !days.value) return;

  db.run(`
    INSERT INTO users(username,start_city,budget,days,preference,result)
    VALUES (?,?,?,?,?,?)
  `,[
    username.value,
    startCity.value,
    +budget.value,
    +days.value,
    preference.value,
    ""
  ]);

  loadUsers();
}

function loadUsers(){
  let res=db.exec("SELECT * FROM users");
  userList.innerHTML="";
  if(!res.length) return;

  res[0].values.forEach(u=>{
    userList.innerHTML+=`
      <li>
        👤 ${u[1]}
        <button onclick="runAI(${u[0]})">PLAN</button>
        <button onclick="deleteUser(${u[0]})">❌</button>
      </li>
    `;
  });
}

function deleteUser(id){
  db.run("DELETE FROM users WHERE id=?",[id]);
  output.textContent="";
  if(polyline) map.removeLayer(polyline);
  drawMarkers();
  loadUsers();
}

/* ================= A* AI ================= */
function runAI(id){
  let u=db.exec("SELECT * FROM users WHERE id=?",[id])[0].values[0];

  let frontier=[{city:u[2],cost:0,day:0,path:[],f:0}];
  let visited=new Set();

  while(frontier.length){
    frontier.sort((a,b)=>a.f-b.f);
    let n=frontier.shift();
    let key=n.city+"-"+n.day;
    if(visited.has(key)) continue;
    visited.add(key);

    let path=[...n.path,n.city];

    if(n.day===u[4]){
      saveResult(id,path,n.cost);
      showResult(path,n.cost);
      animatePath(path);
      return;
    }

    let c=db.exec(
      "SELECT daily_cost,rating,category FROM cities WHERE name=?",
      [n.city]
    )[0].values[0];

    let neigh=db.exec(
      "SELECT to_city,travel_cost FROM distances WHERE from_city=?",
      [n.city]
    );
    if(!neigh.length) continue;

    neigh[0].values.forEach(e=>{
      let newCost=n.cost+e[1]+c[0];
      if(newCost>u[3]) return;

      let g=newCost-(c[1]*25+(c[2]===u[5]?40:0));
      let h=(u[4]-n.day)*50;

      frontier.push({
        city:e[0],
        cost:newCost,
        day:n.day+1,
        path:path,
        f:g+h
      });
    });
  }

  output.textContent="❌ No valid plan found";
}

/* ================= RESULT ================= */
function saveResult(id,path,cost){
  db.run(
    "UPDATE users SET result=? WHERE id=?",
    [path.join(" → ")+" | $"+cost,id]
  );
}

function showResult(path,cost){
  output.textContent="🧠 AI Travel Plan\n\n";
  path.forEach((c,i)=>{
    output.textContent+=`Day ${i+1}: ${c}\n`;
  });
  output.textContent+=`\n💰 Total Cost: $${cost}`;
}

/* ================= ANIMATION ================= */
function animatePath(path){
  let coords=[];
  path.forEach(city=>{
    let r=db.exec(
      "SELECT lat,lng FROM cities WHERE name=?",
      [city]
    )[0].values[0];
    coords.push([r[0],r[1]]);
  });

  if(polyline) map.removeLayer(polyline);

  polyline=L.polyline([coords[0]],{
    color:"green",
    weight:4
  }).addTo(map);

  let i=0;
  let timer=setInterval(()=>{
    i++;
    if(i>=coords.length){
      clearInterval(timer);
      return;
    }
    polyline.addLatLng(coords[i]);
  },400);
}

/* ================= LOAD CITIES ================= */
function loadCities(){
  let res=db.exec("SELECT name FROM cities")[0].values;
  startCity.innerHTML="";
  res.forEach(c=>{
    startCity.innerHTML+=`<option>${c[0]}</option>`;
  });
}

/* ================= EXPORT DB ================= */
function exportDB(){
  let data=db.export();
  let blob=new Blob([data]);
  let a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="travel_ai.db";
  a.click();
}
