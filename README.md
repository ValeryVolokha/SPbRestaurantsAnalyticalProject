
## Environment
#TODO

---

## Requirements
### Mongo installation (macOS)
```bash
# Tap the official MongoDB Homebrew Tap
brew tap mongodb/brew

# Install last mongodb community edition version
brew install mongodb-community

# Start mongodb service
brew services start mongodb-community
```

### Spark installation
It's more convenient to use Spark isolated in a docker container. After steps below, Jupiter notebook will be running on ```http://localhost:8888/``` and spark will be running on port ```4040``` in the docker container, the path to ```SPbRestaurantsAnalyticalProject``` folder with project source code will be mounted to path ```/home/jovyan/work/``` in the container.
```bash
# Install docker
brew cask install docker

# (macOS) Run docker app to launch docker-machine process in background
open -a Docker

# Pull jupyter/pyspark-notebook image and create container
docker run --name pyspark --rm \
            -p 4040:4040 -p 8888:8888 \
            -v /Users/ValeryVolokha/Dev/SPbRestaurantsAnalyticalProject:/home/jovyan/work/ \
            jupyter/pyspark-notebook
```

---

## Reproduction steps
```bash
# Clone the repository
git clone https://github.com/ValeryVolokha/SPbRestaurantsAnalyticalProject

# Enter folder
cd SPbRestaurantsAnalyticalProject

# Install requirements
pip install -r requirements.txt
# or
pip3 install -r requirements.txt
``` 

### (Optional) Scraping and crawling data (warning: may take a long time. It's already done and saved in ```tripadvisor_restaurants.json``` file)
```bash
# Run spider
scrapy crawl TripAdvisor_restaurants
```

As a result, will be created ```tripadvisor_restaurants.json``` file

### Loading data to MongoDB
```bash
# Load data to storage using mongoimport tool to rests collection
mongoimport --jsonArray --db test --collection rests --drop --file tripadvisor_restaurants.json

# (Optional) Check result and scheme
# Run mongo shell
mongo

# Find one object
db.rests.findOne({})
```
Result should looks like:
```json
{
	"_id" : ObjectId("5efdf54261f00ed3fdf69281"),
	"name" : "Meal",
	"address" : "Литейный пр., 17-19, Санкт-Петербург 191028 Россия",
	"district" : "Литейный",
	"rating" : {
		"rating__mean" : 5.0,
		"rating__food" : 5,
		"rating__service" : 5,
		"rating__price_quality" : 5,
		"rating__atmosphere" : 5
	},
	"check_group" : "По умеренной цене",
	"kitchen_types" : [
		"Европейская",
		"Современная"
	]
}
```

---

## Usage

---

## Results