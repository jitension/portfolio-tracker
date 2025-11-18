/**
 * Portfolio Line Chart
 * Displays portfolio value over time with period selector
 */
import React, { useMemo } from 'react';
import { Card, CardContent, Box, Button, ButtonGroup, Typography } from '@mui/material';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import type { HistoricalDataPoint } from '../../../../types/portfolio';

interface PortfolioLineChartProps {
  data: HistoricalDataPoint[];
  selectedPeriod: string;
  onPeriodChange: (period: string) => void;
}

const periods = ['1D', '1W', '1M', '1Y', 'YTD', 'All'];

const PortfolioLineChart: React.FC<PortfolioLineChartProps> = ({
  data,
  selectedPeriod,
  onPeriodChange,
}) => {
  const chartOptions = useMemo(() => {
    // Format data for Highcharts
    const chartData = data.map(point => ({
      x: new Date(point.timestamp).getTime(),
      y: point.value,
    }));

    return {
      chart: {
        type: 'line',
        height: 400,
        backgroundColor: 'transparent',
        style: {
          fontFamily: 'Inter, sans-serif',
        },
      },
      title: {
        text: null,
      },
      xAxis: {
        type: 'datetime',
        labels: {
          style: {
            color: '#999',
          },
        },
        gridLineColor: '#333',
      },
      yAxis: {
        title: {
          text: 'Portfolio Value',
          style: {
            color: '#999',
          },
        },
        labels: {
          style: {
            color: '#999',
          },
          formatter: function(this: any) {
            return '$' + this.value.toLocaleString();
          },
        },
        gridLineColor: '#333',
      },
      series: [{
        name: 'Portfolio Value',
        data: chartData,
        color: '#2E96FF',
        lineWidth: 2,
        marker: {
          enabled: false,
          states: {
            hover: {
              enabled: true,
              radius: 4,
            },
          },
        },
      }],
      tooltip: {
        backgroundColor: '#1a1a1a',
        borderColor: '#444',
        style: {
          color: '#fff',
        },
        formatter: function(this: any) {
          const date = new Date(this.x);
          return `<b>${date.toLocaleDateString()}</b><br/>Value: $${this.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        },
      },
      legend: {
        enabled: false,
      },
      credits: {
        enabled: false,
      },
    };
  }, [data]);

  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="subtitle1">
            Portfolio Performance
          </Typography>
          <ButtonGroup size="small" variant="outlined">
            {periods.map((period) => (
              <Button
                key={period}
                onClick={() => onPeriodChange(period)}
                variant={selectedPeriod === period ? 'contained' : 'outlined'}
              >
                {period}
              </Button>
            ))}
          </ButtonGroup>
        </Box>
        
        {data.length > 0 ? (
          <HighchartsReact highcharts={Highcharts} options={chartOptions} />
        ) : (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography color="text.secondary">
              No historical data available for this period
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default PortfolioLineChart;
