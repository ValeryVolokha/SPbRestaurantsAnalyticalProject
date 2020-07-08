# Analytical project of St. Petersburg restaurants

## Requirements
- ```brew``` pre-installed or install it via:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
```
- ```python 3``` pre-installed or install it via:
```bash
brew install python
```
- ```Docker``` pre-installed or install it via:
```bash
brew cask install docker

# run docker app to launch docker-machine process in background via command or do it manually
open -a Docker
```

---

## Usage
### Clone and start
```bash
# Clone the repository
git clone https://github.com/ValeryVolokha/SPbRestaurantsAnalyticalProject

# Enter folder
cd SPbRestaurantsAnalyticalProject
```

It's more convenient to use isolated docker containers for Spark and MongoDB and ```docker-compose``` utility with ```docker-compose.yml``` file to setting and starting containers. 

```bash
# Start containers
docker-compose up
# or recreate and then start containers if needed to start from scratch
docker-compose up --force-recreate
```

This creates 2 connected pyspark and mongo containers and forwards pyspark container's port 8888 to host's port 9999.

Go to ```http://localhost:9999/``` and open ```/work/analysis.ipynb``` file.

---

## Scraping and crawling data
> Warning: may take a long time. It's already done and saved in ```tripadvisor_restaurants.json``` file.

```bash
# Run spider
docker exec -it mongo bash -c \
	"scrapy crawl TripAdvisor_restaurants"
```

As a result, will be created ```tripadvisor_restaurants.json``` file

### Loading data to MongoDB
#### Easy way: restart containers
```bash
# ctrl/cmd + C to stop containers or use Docker Dashboard GUI

# then start containers back
docker-compose up --force-recreate
```
#### Another way: use ```mongoimport``` tool inside ```mongo``` container
```bash
# Load data to storage using mongoimport tool to rests collection
docker exec -it mongo bash -c \
	"mongoimport --jsonArray \
				 --db test \
				 --collection rests \
				 --drop \
				 --file /work/tripadvisor_restaurants.json"

# Check the result
docker exec -it mongo bash -c 'mongo --eval "db.rests.findOne({})"'
```

The result should contain and looks like:
```json
...
{
	"_id" : "5efdf54261f00ed3fdf69281",
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
	],
	"comments": [
		{
			"comment__rating": 5.0,
			"comment__body": "..."
		},
		{
			"comment__rating": 4.5,
			"comment__body": "..."
		}
		...
	]
}
```
Schema structure:
```
root
 |-- _id: struct
 |    |-- oid: string
 |-- address: string
 |-- check_group: string
 |-- comments: array
 |    |-- element: struct
 |    |    |-- comment__rating: double
 |    |    |-- comment__body: string
 |-- district: string
 |-- kitchen_types: array
 |    |-- element: string
 |-- name: string
 |-- rating: struct
 |    |-- rating__mean: double
 |    |-- rating__food: double
 |    |-- rating__service: double
 |    |-- rating__price_quality: double
 |    |-- rating__atmosphere: double
```

---

## Results