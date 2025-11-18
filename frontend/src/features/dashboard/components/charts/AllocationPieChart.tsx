/**
 * Allocation Pie Chart
 * Displays portfolio allocation by holdings
 */
import React, { useMemo } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import Highcharts from 'highcharts';
import HighchartsReact from 'highcharts-react-official';
import type { AllocationData } from '../../../../types/portfolio';

interface AllocationPieChartProps {
  data: AllocationData[];
}

const AllocationPieChart: React.FC<AllocationPieChartProps> = ({ data }) => {
  const chartOptions = useMemo(() => {
    // Group small holdings (<2%) into "Other"
    const threshold = 2.0;
    const majorHoldings = data.filter(d => d.allocation_percent >= threshold);
    const minorHoldings = data.filter(d => d.allocation_percent < threshold);

    const chartData = majorHoldings.map(holding => ({
      name: holding.symbol,
      y: holding.allocation_percent,
      custom: {
        companyName: holding.company_name,
        marketValue: holding.market_value,
        quantity: holding.quantity,
      },
    }));

    // Add "Other" slice if there are minor holdings
    if (minorHoldings.length > 0) {
      const otherPercent = minorHoldings.reduce((sum, h) => sum + h.allocation_percent, 0);
      chartData.push({
        name: 'Other',
        y: otherPercent,
        custom: {
          companyName: `${minorHoldings.length} small positions`,
          marketValue: minorHoldings.reduce((sum, h) => sum + h.market_value, 0),
          quantity: minorHoldings.length,
        },
      });
    }

    return {
      chart: {
        type: 'pie',
        height: 400,
        backgroundColor: 'transparent',
        style: {
          fontFamily: 'Inter, sans-serif',
        },
      },
      title: {
        text: null,
      },
      plotOptions: {
        pie: {
          allowPointSelect: true,
          cursor: 'pointer',
          dataLabels: {
            enabled: true,
            format: '<b>{point.name}</b><br/>{point.percentage:.1f}%',
            style: {
              color: '#999',
              textOutline: 'none',
            },
          },
          showInLegend: true,
        },
      },
      series: [{
        name: 'Allocation',
        data: chartData,
        colorByPoint: true,
      }],
      tooltip: {
        backgroundColor: '#1a1a1a',
        borderColor: '#444',
        style: {
          color: '#fff',
        },
        formatter: function(this: any) {
          return `<b>${this.point.name}</b><br/>
            ${this.point.custom.companyName}<br/>
            Allocation: ${this.point.percentage.toFixed(1)}%<br/>
            Value: $${this.point.custom.marketValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        },
      },
      legend: {
        align: 'right',
        verticalAlign: 'middle',
        layout: 'vertical',
        itemStyle: {
          color: '#999',
        },
        itemHoverStyle: {
          color: '#fff',
        },
      },
      credits: {
        enabled: false,
      },
    };
  }, [data]);

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle1" sx={{ mb: 2 }}>
          Portfolio Allocation
        </Typography>
        
        {data.length > 0 ? (
          <HighchartsReact highcharts={Highcharts} options={chartOptions} />
        ) : (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography color="text.secondary">
              No holdings to display
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AllocationPieChart;
