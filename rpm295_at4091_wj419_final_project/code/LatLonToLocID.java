import java.util.*;
import java.io.*;

public class LatLonToLocID 
{
	public static void main(String[] args) throws IOException
	{
		Double[] lat = new Double[265];
		Double[] lon = new Double [265];
		String csvFile = "taxi_zone_lonlat.csv";
		String cvsSplitBy = ",";
		BufferedReader br = new BufferedReader(new FileReader(csvFile));
		File file = new File("./2015_locIDs.csv");
		FileWriter fw = new FileWriter(file);
		String line = br.readLine();
		int i = 0;
        while ((line = br.readLine()) != null) 
        {
            String[] cols = line.split(cvsSplitBy);
            lat[i] = Double.parseDouble(cols[4]);
            lon[i++] = Double.parseDouble(cols[5]);
        }
		csvFile = "./2015_taxi.csv";
		br = new BufferedReader(new FileReader(csvFile));
		line = br.readLine();
		//int q = 0;
		while ((line = br.readLine()) != null) 
        {
        	//if (q++ % 1000 == 0)
        	//	System.out.println(q);
            String[] cols = line.split(cvsSplitBy);
            // pickup
            Double lat1 = Double.parseDouble(cols[2]);
            Double lon1 = Double.parseDouble(cols[1]);
            int minLocID = 0;
            Double minDist = Double.MAX_VALUE; 
            for (int j = 0; j < lat.length; j++)
            {
            	Double lat2 = lat[j];
            	Double lon2 = lon[j];
            	Double x = (lon2 - lon1) * Math.cos((lat1 + lat2)/2);
			    Double y = (lat2 - lat1);
			    Double c = x*x + y*y;
			    if (c < minDist)
			    {
			      minDist = c;
			      minLocID = j;
    			}
            }
            fw.write(line + ",");
            fw.write((minLocID + 1) + ", ");
            // dropoff
            lat1 = Double.parseDouble(cols[4]);
            lon1 = Double.parseDouble(cols[3]);
            minDist = Double.MAX_VALUE; 
            for (int j = 0; j < lat.length; j++)
            {
            	Double lat2 = lat[j];
            	Double lon2 = lon[j];
            	Double x = (lon2 - lon1) * Math.cos((lat1 + lat2)/2);
			    Double y = (lat2 - lat1);
			    Double c = x*x + y*y;
			    if (c < minDist)
			    {
			      minDist = c;
			      minLocID = j;
    			}
            }
            fw.write((minLocID + 1) + "\n");
        }
	}
}