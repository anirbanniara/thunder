package thunder.util

import org.apache.spark.rdd.RDD
import cern.colt.matrix._
import cern.colt.matrix.linalg._
import cern.jet.math._

class MatrixRDD(val mat: RDD[DoubleMatrix1D]) extends Serializable {

    val alg = Algebra.DEFAULT
    val factory1D = DoubleFactory1D.dense
    val factory2D = DoubleFactory2D.dense

    // class for n x d 2D matrices stored as RDDs of 1 x d 1D matrices
    // efficient only when n >> d

    def + (other: MatrixRDD) : MatrixRDD = {
      // add two RDD matrices element-wise
      return new MatrixRDD(this.mat.zip(other.mat).map{case (x1,x2) => x1.assign(x2,Functions.plus)})
    }

    def - (other: MatrixRDD) : MatrixRDD = {
      // subtract two RDD matrices element-wise
      new MatrixRDD(this.mat.zip(other.mat).map{case (x1,x2) => x1.assign(x2,Functions.minus)})
    }

    def * (other: DoubleMatrix2D) : MatrixRDD = {
      // multiply an RDD matrix by a smaller matrix
      new MatrixRDD(this.mat.map(x => alg.mult(alg.transpose(other),x)))
    }

    def ** (other: MatrixRDD) : DoubleMatrix2D = {
      // multiply one RDD matrix by the transpose of another one
      this.mat.zip(other.mat).map{case (x,y) => outerProd(x,y)}.reduce(_.assign(_,Functions.plus))
    }

    def / (other: DoubleMatrix2D) : MatrixRDD = {
      // right matrix division
      return this * alg.transpose(alg.inverse(alg.transpose(other)))
    }

    def svd (k: Int, m: Int): (MatrixRDD, DoubleMatrix2D) = {
      // get the svd of an RDD matrix
      val cov = this.mat.map(x => outerProd(x,x)).reduce(_.assign(_,Functions.plus))
      val svd = new SingularValueDecomposition(cov)
      val s = factory1D.make(svd.getSingularValues().take(k).map(x => 1 / scala.math.sqrt(x)))
      val inds = Range(0,k).toArray
      val V = svd.getU().viewSelection(Range(0,m).toArray,inds)
      val multFac = alg.mult(V,factory2D.diagonal(s))
      val U = this * multFac
      return (U,V)
    }

    def add (other: MatrixRDD) = this + other

    def subtract (other: MatrixRDD) = this - other

    def toStringArray : Array[String] = {
      return this.mat.toArray().map(x => x.toArray().mkString(" "))
    }

    def outerProd(vec1: DoubleMatrix1D, vec2: DoubleMatrix1D): DoubleMatrix2D = {
      val out = factory2D.make(vec1.size,vec2.size)
      alg.multOuter(vec1,vec2,out)
      return out
    }

  }

