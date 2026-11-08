%dw 2.0
output json
import * from dw::Weather


fun weatherMessage(todayWeather: Weather) = 
    "The weather for today is: " ++ todayWeather
var worstPossibleWeather: DetailedWeather = {temperature: -10, weather: "stormy"}
---
{
    a: weatherMessage("sunny"),
    b: worstPossibleWeather.weather is Weather
}