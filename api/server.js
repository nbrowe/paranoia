/* Configure express server. */
const express = require('express');
const http = require('http');
const client = express();
const port = process.env.PORT || 5000;
const cors = require('cors');
const path = require('path');
const axios = require('axios');

// const server = http.createServer(client);

client.use(cors());

client.get('/giphy', (req, res) => {
  // console.log(`Searching for a gif with the term: ${req.query.term}`);

  // let params = req.query.term.replace(/ /g, '+');
  // console.log(params);
  // params += '&api_key=5Bdp0z2z28aSDNkcbuqPQAsMXZBoXIXj';
  // params += '&limit=10';

  // axios.get(`https://api.giphy.com/v1/gifs/search?q=${params}`)
  //   .then(function (response) {
  //     res.send({
  //       success: true,
  //       data: response.data.data
  //     })

  //   })
  //   .catch(function (error) {
  //     res.send({
  //       success: false,
  //       data: []
  //     })
  //     console.log("error occurred");
  //   });

  res.send({
    success: true,
    data: ['a','b','c']
  });
});

client.use(express.static('public'));
client.use('*', (req, res) => {
  res.sendFile(path.resolve(__dirname, 'public', 'index.html'));
});

client.listen(port, () => {
  console.log(`Server started at port ${port}`);
})